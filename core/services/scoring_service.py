import copy
import logging
from typing import Dict, Tuple
from .nlp_service import nlp_service
from .gemini_service import gemini_service
from core.models import AdminSettings


logger = logging.getLogger(__name__)


class ScoringService:
    def __init__(self):
        self.nlp = nlp_service
        self.gemini = gemini_service
    
    def compute_match_score(
        self, 
        resume_text: str, 
        jd_text: str, 
        resume_sections: Dict = None, 
        jd_sections: Dict = None
    ) -> Dict:
        logger.debug("[SCORING] Starting match score computation...")
        
        if not resume_sections:
            logger.debug("[SCORING] Resume sections not provided, parsing...")
            resume_sections = self.nlp.parse_resume_sections(resume_text)
        
        if not jd_sections:
            logger.debug("[SCORING] JD sections not provided, parsing...")
            jd_sections = self.nlp.parse_jd_sections(jd_text)
        
        logger.debug("[SCORING] Loading admin settings...")
        settings = AdminSettings.get_settings()
        logger.debug(
            "[SCORING] Settings loaded - Weights: Education=%s, Skills=%s, Experience=%s",
            settings.weight_education,
            settings.weight_skills,
            settings.weight_experience
        )
        
        logger.debug("[SCORING] Computing profession similarity...")
        profession_similarity = self.nlp.compute_profession_similarity(
            resume_text, jd_text
        )
        logger.debug("[SCORING] Profession similarity: %.3f", profession_similarity)
        
        initial_profession_mismatch = False
        profession_override_reason = None
        initial_profession_flagged = False
        if profession_similarity < settings.profession_zero_threshold:
            initial_profession_mismatch = True
            initial_profession_flagged = True
            logger.info(
                "[SCORING] Profession mismatch detected (similarity %.3f < threshold %.3f)",
                profession_similarity,
                settings.profession_zero_threshold
            )
        
        logger.debug("[SCORING] Computing education similarity...")
        education_score = self.nlp.compute_education_similarity(
            resume_sections['education'],
            jd_sections['education']
        )
        logger.debug("[SCORING] Education score: %.3f", education_score)
        
        logger.debug("[SCORING] Computing skills similarity...")
        skills_score, skills_breakdown = self.nlp.compute_skills_similarity(
            resume_sections['skills'],
            jd_sections['skills']
        )
        logger.debug(
            "[SCORING] Skills score: %.3f, Matched: %d, Missing: %d",
            skills_score,
            len(skills_breakdown.get('matched', [])),
            len(skills_breakdown.get('missing', []))
        )

        matched_count = len(skills_breakdown.get('matched', []))
        missing_count = len(skills_breakdown.get('missing', []))
        jd_skill_total = matched_count + missing_count
        skill_overlap_ratio = matched_count / jd_skill_total if jd_skill_total else 0.0
        skills_breakdown['match_ratio_value'] = round(skill_overlap_ratio, 3)

        if initial_profession_mismatch and skill_overlap_ratio >= 0.5:
            logger.info(
                "[SCORING] Overriding profession mismatch due to skill overlap (%.2f)",
                skill_overlap_ratio
            )
            initial_profession_mismatch = False
            profession_override_reason = 'High skill overlap with JD'
        
        logger.debug("[SCORING] Computing experience similarity...")
        experience_score = self.nlp.compute_experience_similarity(
            resume_sections['experience'],
            jd_sections['experience']
        )
        logger.debug("[SCORING] Experience score: %.3f", experience_score)
        
        raw_bert_score = (
            settings.weight_education * education_score +
            settings.weight_skills * skills_score +
            settings.weight_experience * experience_score
        )
        
        bert_final_score = raw_bert_score * 100
        bert_baseline_final = bert_final_score
        capped = False
        
        if initial_profession_mismatch:
            logger.info("[SCORING] Zeroing composite score due to profession mismatch")
            bert_final_score = 0.0
        elif profession_similarity < settings.profession_cap_threshold:
            # allow higher cap when skills strongly overlap
            dynamic_cap = settings.partial_credit_cap
            if skill_overlap_ratio >= 0.5:
                dynamic_cap = min(100.0, settings.partial_credit_cap * 1.5)
            bert_final_score = min(bert_final_score, dynamic_cap)
            capped = True
            logger.debug("[SCORING] Applied dynamic cap: %.2f", dynamic_cap)
        
        bert_scores_for_prompt = {
            'education': round(education_score, 3),
            'skills': round(skills_score, 3),
            'experience': round(experience_score, 3),
            'final': round(bert_final_score, 2)
        }
        logger.debug(
            "[SCORING] BERT scores computed - Final: %.2f, Capped: %s",
            bert_final_score,
            capped
        )
        
        logger.debug("[SCORING] Calling Gemini for validation...")
        gemini_correction = self.gemini.validate_match_scores(
            resume_sections,
            jd_sections,
            bert_scores_for_prompt,
            profession_similarity
        )
        if gemini_correction:
            gemini_correction = copy.deepcopy(gemini_correction)
        logger.debug("[SCORING] Gemini correction received: %s", gemini_correction is not None)
        
        mismatch_suggestion = 'This position requires experience in a different field. Consider applying to jobs that match your professional background.'
        default_suggestion = self._generate_default_suggestion(
            skills_breakdown, education_score, experience_score
        )
        
        if initial_profession_mismatch:
            final_score = 0.0
            suggestion_text = mismatch_suggestion
            logger.info("[SCORING] Profession mismatch in effect; awaiting AI review for possible override")
        else:
            final_score = bert_final_score
            suggestion_text = default_suggestion
            logger.debug("[SCORING] Using BERT score prior to AI validation: %.2f", final_score)

        final_profession_mismatch = initial_profession_mismatch
        profession_reason = None
        ai_profession_flag_resolved = None
        
        review_text = None
        tip_text = None

        if gemini_correction and 'final_score' in gemini_correction:
            gemini_final_score = min(max(gemini_correction['final_score'], 0.0), 100.0)
            final_score = gemini_final_score
            ai_profession_flag = gemini_correction.get('profession_mismatch')
            if ai_profession_flag is not None:
                if isinstance(ai_profession_flag, str):
                    ai_profession_flag_resolved = ai_profession_flag.strip().lower() in {'true', '1', 'yes'}
                else:
                    ai_profession_flag_resolved = bool(ai_profession_flag)
                final_profession_mismatch = ai_profession_flag_resolved
            profession_reason = gemini_correction.get('profession_reason') or profession_reason
            if initial_profession_mismatch and not final_profession_mismatch:
                logger.info("[SCORING] AI reviewer cleared the initial profession mismatch with score: %.2f", final_score)
            elif final_profession_mismatch:
                logger.info("[SCORING] AI reviewer confirmed profession mismatch; score: %.2f", final_score)
            else:
                logger.debug("[SCORING] AI reviewer adjusted score to: %.2f", final_score)
            review_text = gemini_correction.get('review')
            tip_text = gemini_correction.get('suggestion')
            if review_text:
                suggestion_text = review_text.strip()
            else:
                suggestion_text = gemini_correction.get('suggestion', suggestion_text)
        else:
            logger.warning("[SCORING] AI reviewer unavailable; keeping score: %.2f", final_score)

        if not gemini_correction:
            profession_reason = None

        if not final_profession_mismatch and suggestion_text == mismatch_suggestion:
            suggestion_text = default_suggestion

        if final_profession_mismatch and not profession_reason:
            profession_reason = mismatch_suggestion
        elif not final_profession_mismatch and profession_reason is None and initial_profession_flagged:
            profession_reason = 'AI reviewer confirmed the role aligns with your profile.'
        elif not final_profession_mismatch and profession_reason is None and profession_override_reason:
            profession_reason = profession_override_reason

        if final_profession_mismatch and suggestion_text == default_suggestion:
            suggestion_text = profession_reason or mismatch_suggestion

        mismatch_cap = 5.0
        mismatch_cap_applied = False
        if final_profession_mismatch and final_score > mismatch_cap:
            original_final_score = final_score
            final_score = mismatch_cap
            mismatch_cap_applied = True
            if gemini_correction:
                gemini_correction['final_score_original'] = original_final_score
                gemini_correction['final_score'] = mismatch_cap
            logger.info(
                "[SCORING] Profession mismatch cap applied: original %.2f -> capped %.2f",
                original_final_score,
                mismatch_cap
            )

        breakdown_details = {
            'skills_breakdown': skills_breakdown,
            'education_match': education_score > 0.7,
            'experience_match': experience_score > 0.7,
            'profession_similarity': round(profession_similarity, 3),
            'transferable_skills': capped,
            'weights_used': {
                'education': settings.weight_education,
                'skills': settings.weight_skills,
                'experience': settings.weight_experience
            },
            'bert_baseline_final': round(bert_baseline_final, 2),
            'profession_mismatch': final_profession_mismatch,
            'initial_profession_mismatch': initial_profession_flagged,
            'profession_reason': profession_reason,
            'ai_profession_mismatch': ai_profession_flag_resolved,
            'improvement_tip': tip_text.strip() if gemini_correction and tip_text else None
        }
        if profession_override_reason:
            breakdown_details['profession_override_reason'] = profession_override_reason
        if final_profession_mismatch:
            breakdown_details['message'] = profession_reason or mismatch_suggestion
        if mismatch_cap_applied:
            breakdown_details['mismatch_cap_applied'] = mismatch_cap
        
        bert_scores = {
            'education': round(education_score, 3),
            'skills': round(skills_score, 3),
            'experience': round(experience_score, 3),
            'final': round(final_score, 2),
            'baseline_final': round(bert_baseline_final, 2)
        }

        result = {
            'bert_scores': bert_scores,
            'profession_similarity': round(profession_similarity, 3),
            'profession_match_flag': not final_profession_mismatch,
            'final_score': round(final_score, 2),
            'breakdown_details': breakdown_details,
            'gemini_correction': gemini_correction,
            'suggestion_text': suggestion_text
        }
        logger.debug("[SCORING] Match computation complete - Final score: %.2f", result['final_score'])
        return result
    
    def _generate_default_suggestion(
        self, 
        skills_breakdown: Dict, 
        education_score: float, 
        experience_score: float
    ) -> str:
        suggestions = []
        
        if skills_breakdown.get('missing'):
            missing_count = len(skills_breakdown['missing'])
            if missing_count > 0:
                top_missing = skills_breakdown['missing'][:3]
                suggestions.append(
                    f"Consider gaining experience in: {', '.join(top_missing)}"
                )
        
        if education_score < 0.5:
            suggestions.append(
                "Consider pursuing additional certifications or degrees relevant to this role"
            )
        
        if experience_score < 0.5:
            suggestions.append(
                "Highlight more relevant work experience or projects in your resume"
            )
        
        if not suggestions:
            suggestions.append(
                "Your profile is a good match. Consider tailoring your resume to emphasize key achievements."
            )
        
        return ". ".join(suggestions) + "."


scoring_service = ScoringService()
