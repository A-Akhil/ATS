from typing import Dict, Tuple
from .nlp_service import nlp_service
from .gemini_service import gemini_service
from core.models import AdminSettings


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
        if not resume_sections:
            resume_sections = self.nlp.parse_resume_sections(resume_text)
        
        if not jd_sections:
            jd_sections = self.nlp.parse_jd_sections(jd_text)
        
        settings = AdminSettings.get_settings()
        
        profession_similarity = self.nlp.compute_profession_similarity(
            resume_text, jd_text
        )
        
        if profession_similarity < settings.profession_zero_threshold:
            return {
                'bert_scores': {
                    'education': 0.0,
                    'skills': 0.0,
                    'experience': 0.0,
                    'final': 0.0
                },
                'profession_similarity': profession_similarity,
                'profession_match_flag': False,
                'final_score': 0.0,
                'breakdown_details': {
                    'profession_mismatch': True,
                    'message': 'Profession mismatch - Resume does not match job requirements'
                },
                'gemini_correction': None,
                'suggestion_text': 'This position requires experience in a different field. Consider applying to jobs that match your professional background.'
            }
        
        education_score = self.nlp.compute_education_similarity(
            resume_sections['education'],
            jd_sections['education']
        )
        
        skills_score, skills_breakdown = self.nlp.compute_skills_similarity(
            resume_sections['skills'],
            jd_sections['skills']
        )
        
        experience_score = self.nlp.compute_experience_similarity(
            resume_sections['experience'],
            jd_sections['experience']
        )
        
        raw_bert_score = (
            settings.weight_education * education_score +
            settings.weight_skills * skills_score +
            settings.weight_experience * experience_score
        )
        
        bert_final_score = raw_bert_score * 100
        
        if profession_similarity < settings.profession_cap_threshold:
            bert_final_score = min(bert_final_score, settings.partial_credit_cap)
            capped = True
        else:
            capped = False
        
        bert_scores = {
            'education': round(education_score, 3),
            'skills': round(skills_score, 3),
            'experience': round(experience_score, 3),
            'final': round(bert_final_score, 2)
        }
        
        gemini_correction = self.gemini.validate_match_scores(
            resume_sections,
            jd_sections,
            bert_scores,
            profession_similarity
        )
        
        if gemini_correction and 'final_score' in gemini_correction:
            final_score = gemini_correction['final_score']
            suggestion_text = gemini_correction.get('suggestion', '')
        else:
            final_score = bert_final_score
            suggestion_text = self._generate_default_suggestion(
                skills_breakdown, education_score, experience_score
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
            }
        }
        
        return {
            'bert_scores': bert_scores,
            'profession_similarity': round(profession_similarity, 3),
            'profession_match_flag': True,
            'final_score': round(final_score, 2),
            'breakdown_details': breakdown_details,
            'gemini_correction': gemini_correction,
            'suggestion_text': suggestion_text
        }
    
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
