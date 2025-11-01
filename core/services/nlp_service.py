import logging
import numpy as np
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


logger = logging.getLogger(__name__)


class NLPService:
    def __init__(self):
        try:
            logger.debug("[NLP] Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.debug("[NLP] SentenceTransformer model loaded successfully")
        except Exception as e:
            logger.exception("[NLP] Error loading sentence transformer")
            self.model = None
        # Degree hierarchy used for education comparisons (higher number = higher degree)
        self.level_hierarchy = {
            'unknown': 0,
            'diploma': 1,
            'bachelor': 2,
            'master': 3,
            'doctoral': 4,
        }
        # Keywords to segment resumes/JDs into logical blocks before extraction
        self.section_keywords = {
            'education': [
                'education', 'academic background', 'academics', 'qualifications',
                'educational background', 'academic profile'
            ],
            'experience': [
                'experience', 'work experience', 'professional experience', 'employment history',
                'work history', 'career history', 'professional background'
            ],
            'skills': [
                'skills', 'technical skills', 'core competencies', 'technologies', 'tools',
                'skillset', 'tech stack', 'technical proficiency'
            ]
        }
    
    def normalize_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _segment_document(self, text: str) -> Dict[str, str]:
        """Lightweight heuristic to capture Education/Experience/Skills snippets."""
        sections: Dict[str, List[str]] = {key: [] for key in self.section_keywords}
        current_key: Optional[str] = None

        lines = text.splitlines()
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            normalized_line = line.lower()

            matched_section = None
            for key, keywords in self.section_keywords.items():
                for keyword in keywords:
                    if normalized_line.startswith(keyword) or normalized_line.startswith(f"{keyword}:"):
                        matched_section = key
                        break
                    # handle headings formatted like "### Skills" or "— SKILLS"
                    if normalized_line == keyword:
                        matched_section = key
                        break
                if matched_section:
                    break

            if matched_section:
                current_key = matched_section
                continue

            if current_key:
                sections[current_key].append(line)

        return {key: '\n'.join(values).strip() for key, values in sections.items() if values}

    def _detect_highest_degree(self, levels: List[str]) -> str:
        if not levels:
            return 'unknown'
        return max(levels, key=lambda lvl: self.level_hierarchy.get(lvl, 0))

    def _extract_years(self, normalized_text: str) -> float:
        years_found = []

        range_pattern = re.findall(r'(\d+(?:\.\d+)?)\s*[-–to]{1,3}\s*(\d+(?:\.\d+)?)\s*(?:years|year|yrs|yr)', normalized_text)
        for start, end in range_pattern:
            try:
                years_found.append(float(end))
            except ValueError:
                continue

        plus_pattern = re.findall(r'(\d+(?:\.\d+)?)\s*\+\s*(?:years|year|yrs|yr)', normalized_text)
        for match in plus_pattern:
            try:
                years_found.append(float(match))
            except ValueError:
                continue

        comparative_pattern = re.findall(
            r'(?:at least|minimum|min|over|more than|greater than)\s+(\d+(?:\.\d+)?)\s*(?:years|year|yrs|yr)',
            normalized_text
        )
        for match in comparative_pattern:
            try:
                years_found.append(float(match))
            except ValueError:
                continue

        direct_pattern = re.findall(r'(\d+(?:\.\d+)?)\s*(?:years|year|yrs|yr)', normalized_text)
        for match in direct_pattern:
            try:
                years_found.append(float(match))
            except ValueError:
                continue

        estimated_years = self._estimate_years_from_dates(normalized_text)
        if estimated_years:
            years_found.append(estimated_years)

        if not years_found:
            return 0.0

        return max(years_found)

    def _estimate_years_from_dates(self, normalized_text: str) -> Optional[float]:
        month_map = {
            'jan': 1, 'january': 1,
            'feb': 2, 'february': 2,
            'mar': 3, 'march': 3,
            'apr': 4, 'april': 4,
            'may': 5,
            'jun': 6, 'june': 6,
            'jul': 7, 'july': 7,
            'aug': 8, 'august': 8,
            'sep': 9, 'sept': 9, 'september': 9,
            'oct': 10, 'october': 10,
            'nov': 11, 'november': 11,
            'dec': 12, 'december': 12,
        }

        tokens = normalized_text.split()
        spans = []
        i = 0
        while i < len(tokens) - 1:
            token = tokens[i]
            if token in month_map and i + 1 < len(tokens):
                start_month = month_map[token]
                start_year_token = tokens[i + 1]
                if start_year_token.isdigit() and len(start_year_token) == 4:
                    start_year = int(start_year_token)
                    j = i + 2
                    end_month = start_month
                    end_year = start_year
                    while j < len(tokens):
                        candidate = tokens[j]
                        if candidate in {'to', 'through', 'till', 'until', '-', '–'}:
                            j += 1
                            continue
                        if candidate in month_map and j + 1 < len(tokens) and tokens[j + 1].isdigit():
                            end_month = month_map[candidate]
                            end_year = int(tokens[j + 1])
                            j += 2
                            break
                        if candidate == 'present' or candidate == 'current':
                            current_date = datetime.utcnow()
                            end_month = current_date.month
                            end_year = current_date.year
                            j += 1
                            break
                        if candidate.isdigit() and len(candidate) == 4:
                            end_year = int(candidate)
                            j += 1
                            break
                        j += 1

                    span = ((start_year, start_month), (end_year, end_month))
                    spans.append(span)
                    i = j
                    continue
            i += 1

        if not spans:
            return None

        total_months = 0
        overall_start = None
        overall_end = None
        for (sy, sm), (ey, em) in spans:
            start_total = sy * 12 + (sm - 1)
            end_total = ey * 12 + (em - 1)
            if end_total < start_total:
                continue
            total_months += (end_total - start_total + 1)
            if overall_start is None or start_total < overall_start:
                overall_start = start_total
            if overall_end is None or end_total > overall_end:
                overall_end = end_total

        if total_months <= 0:
            return None

        overall_years = 0.0
        if overall_start is not None and overall_end is not None and overall_end >= overall_start:
            overall_years = (overall_end - overall_start + 1) / 12.0

        return max(total_months / 12.0, overall_years)

    def _extract_job_titles(self, normalized_text: str) -> List[str]:
        job_title_pattern = re.compile(
            r'(?:senior|lead|principal|staff|software|full stack|fullstack|backend|front end|frontend|data|machine learning|ml|cloud|devops|site reliability|qa|quality assurance|product|project|program|security|platform|mobile|android|ios|web)?\s*(?:engineer|developer|scientist|analyst|manager|architect|consultant|specialist|administrator|designer)',
            re.IGNORECASE
        )
        titles = set()
        for match in job_title_pattern.finditer(normalized_text):
            title = self.normalize_text(match.group()).strip()
            if title:
                titles.add(title)
        return list(titles)
    
    def extract_education(self, text: str) -> Dict:
        normalized = self.normalize_text(text)
        degree_patterns = {
            'doctoral': [r'\bphd\b', r'\bph\.d\b', r'\bdoctorate\b', r'\bdoctoral\b'],
            'master': [
                r'\bmaster\b', r'\bmasters\b', r'\bm\.?s\.?\b', r'\bm\.?a\.?\b',
                r'\bm\.?sc\.?\b', r'\bm\.?tech\b', r'\bmba\b', r'\bm\.?b\.?a\.?\b'
            ],
            'bachelor': [
                r'\bbachelor\b', r"\bbachelor's\b", r'\bb\.?s\.?\b', r'\bb\.?a\.?\b',
                r'\bb\.?sc\.?\b', r'\bb\.?tech\b', r'\bb\.?e\.?\b', r'\bbeng\b', r'\bbsc\b'
            ],
            'diploma': [r'\bdiploma\b', r'\bassociate\b', r'\bcertificate\b']
        }

        matched_levels: List[str] = []
        for level, patterns in degree_patterns.items():
            for pattern in patterns:
                if re.search(pattern, normalized):
                    matched_levels.append(level)
                    break

        tokens = normalized.split()
        bigrams = {' '.join(tokens[i:i + 2]) for i in range(len(tokens) - 1)}
        trigrams = {' '.join(tokens[i:i + 3]) for i in range(len(tokens) - 2)}

        degree_aliases = {
            'doctoral': {'doctor of philosophy'},
            'master': {'m tech', 'm sc', 'msc', 'm s', 'ms', 'm a', 'ma', 'post graduate', 'postgraduate', 'graduate studies'},
            'bachelor': {'b tech', 'b sc', 'bsc', 'b s', 'bs', 'b e', 'be', 'undergraduate', 'bachelor of technology', 'bachelor of science'},
            'diploma': {'associate degree', 'diploma'}
        }

        for level, aliases in degree_aliases.items():
            if aliases & bigrams or aliases & trigrams:
                matched_levels.append(level)

        highest_level = self._detect_highest_degree(matched_levels)

        return {
            'degree_level': highest_level,
            'degrees': list(dict.fromkeys(matched_levels)),
            'raw_text': text.strip(),
            'normalized_text': normalized
        }
    
    def extract_skills(self, text: str) -> List[str]:
        normalized = self.normalize_text(text)
        lower_text = text.lower()

        common_skills = [
            'python', 'java', 'javascript', 'c++', 'cpp', 'c#', 'ruby', 'php', 'swift', 'kotlin',
            'react', 'angular', 'vue', 'node', 'express', 'django', 'flask', 'spring',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'github', 'gitlab',
            'machine learning', 'deep learning', 'nlp', 'computer vision', 'data science',
            'tensorflow', 'pytorch', 'keras', 'scikit learn', 'pandas', 'numpy',
            'html', 'css', 'sass', 'bootstrap', 'tailwind', 'typescript', 'golang', 'rust', 'linux',
            'rest api', 'graphql', 'microservices', 'agile', 'scrum', 'devops',
            'leadership', 'communication', 'problem solving', 'teamwork', 'project management'
        ]

        found_skills = set()
        for skill in common_skills:
            if skill in normalized:
                found_skills.add(skill)

        tech_patterns = [
            r'\b[a-z0-9\+\#\.\-]+\.js\b',
            r'\b[a-z0-9\+\#\.\-]+sql\b',
            r'\b[a-z0-9\+\#\.\-]+db\b',
            r'\bc\+\+\b',
            r'\bc#\b',
            r'\baws\b', r'\bazure\b', r'\bgcp\b'
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, lower_text)
            for match in matches:
                canonical = match.strip()
                found_skills.add(canonical)
                if canonical.endswith('.js'):
                    base = canonical.replace('.js', '')
                    found_skills.add(base)
                if canonical in {'c#', 'csharp'}:
                    found_skills.add('csharp')
                    found_skills.add('c#')
                if canonical == 'c++':
                    found_skills.add('cpp')
                if canonical in {'reactjs', 'react.js'}:
                    found_skills.add('react')
                if canonical in {'nextjs', 'next.js'}:
                    found_skills.add('nextjs')
                if canonical in {'nodejs', 'node.js'}:
                    found_skills.add('node')
                if canonical in {'expressjs', 'express.js'}:
                    found_skills.add('express')
                if canonical.endswith('sql') and canonical != 'sql':
                    found_skills.add('sql')

        bullet_tokens = re.split(r'[\n,;•\|\/\-]+', text)
        for token in bullet_tokens:
            cleaned = self.normalize_text(token)
            if len(cleaned) < 2:
                continue
            if cleaned in common_skills:
                found_skills.add(cleaned)
                continue
            if cleaned.endswith(' js'):
                found_skills.add(cleaned.replace(' js', ''))
            if cleaned in {'reactjs', 'react js'}:
                found_skills.add('react')
            if cleaned in {'nextjs', 'next js'}:
                found_skills.add('nextjs')
            if cleaned in {'nodejs', 'node js'}:
                found_skills.add('node')
            if cleaned in {'expressjs', 'express js'}:
                found_skills.add('express')
            if cleaned.endswith(' sql'):
                found_skills.add('sql')
            for skill in common_skills:
                if skill in cleaned and len(skill) > 2:
                    found_skills.add(skill)

        return list(found_skills)
    
    def extract_job_requirements(self, text: str) -> List[str]:
        lines = text.splitlines()
        requirements: List[str] = []
        seen: set[str] = set()

        heading_triggers = [
            'requirement', 'qualification', 'responsibilit', 'what you will do',
            'what you will need', 'skills you will need', 'preferred skills',
            'skills and experience', 'role requirements'
        ]
        capture_block = False

        for raw_line in lines:
            stripped = raw_line.strip()
            if not stripped:
                continue

            normalized_line = stripped.lower()
            is_heading = stripped.endswith(':') and len(stripped.split()) <= 6

            if is_heading:
                if any(keyword in normalized_line for keyword in heading_triggers):
                    capture_block = True
                else:
                    capture_block = False
                continue

            if any(keyword in normalized_line for keyword in heading_triggers) and len(stripped.split()) <= 6:
                capture_block = True
                continue

            if not capture_block:
                continue

            clean_line = re.sub(r'^[\-\*\u2022\•]+\s*', '', stripped)
            clean_line = re.sub(r'^\d+[\.)]\s*', '', clean_line)
            clean_line = clean_line.strip()
            if not clean_line:
                continue

            normalized_item = self.normalize_text(clean_line)
            if normalized_item and normalized_item not in seen:
                requirements.append(clean_line)
                seen.add(normalized_item)

        return requirements
    
    def extract_experience(self, text: str) -> Dict:
        normalized = self.normalize_text(text)

        years = self._extract_years(normalized)
        job_titles = self._extract_job_titles(normalized)

        return {
            'years': years,
            'job_titles': job_titles,
            'raw_text': text.strip(),
            'normalized_text': normalized
        }
    
    def parse_resume_sections(self, text: str) -> Dict:
        logger.debug("[NLP] Parsing resume sections...")
        segmented = self._segment_document(text)
        result = {
            'education': self.extract_education(segmented.get('education', text)),
            'skills': self.extract_skills(segmented.get('skills', text)),
            'experience': self.extract_experience(segmented.get('experience', text))
        }
        logger.debug(
            "[NLP] Resume sections parsed - Education: %s, Skills: %d, Experience: %.2f years",
            result['education']['degree_level'],
            len(result['skills']),
            result['experience']['years']
        )
        return result
    
    def parse_jd_sections(self, text: str) -> Dict:
        logger.debug("[NLP] Parsing JD sections...")
        segmented = self._segment_document(text)
        requirements_list = self.extract_job_requirements(text)
        requirements_text = "\n".join(requirements_list)

        skills_source = segmented.get('skills', text)
        jd_skills = self.extract_skills(skills_source)
        if requirements_text:
            derived_skills = self.extract_skills(requirements_text)
            if derived_skills:
                jd_skills = list(dict.fromkeys(jd_skills + derived_skills))

        experience_source = segmented.get('experience', '') or ''
        if requirements_text:
            experience_source = f"{experience_source}\n{requirements_text}" if experience_source else requirements_text
        jd_experience = self.extract_experience(experience_source or text)

        result = {
            'education': self.extract_education(segmented.get('education', text)),
            'skills': jd_skills,
            'experience': jd_experience,
            'requirements': requirements_list
        }
        if jd_skills:
            preview = ', '.join(jd_skills[:10])
            logger.debug("[NLP] JD skills extracted: %s", preview)
        logger.debug(
            "[NLP] JD sections parsed - Education: %s, Skills: %d, Experience: %.2f years, Requirements: %d",
            result['education']['degree_level'],
            len(result['skills']),
            result['experience']['years'],
            len(result['requirements'])
        )
        return result
    
    def compute_embeddings(self, texts: List[str]) -> np.ndarray:
        if not self.model:
            logger.warning("[NLP] Model not loaded, returning zero embeddings")
            return np.zeros((len(texts), 384))
        logger.debug("[NLP] Computing embeddings for %d text(s)...", len(texts))
        embeddings = self.model.encode(texts)
        logger.debug("[NLP] Embeddings computed: shape %s", embeddings.shape)
        return embeddings
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0
        
        embeddings = self.compute_embeddings([text1, text2])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(similarity)
    
    def compute_education_similarity(self, resume_edu: Dict, jd_edu: Dict) -> float:
        resume_text = resume_edu.get('normalized_text') or self.normalize_text(resume_edu.get('raw_text', ''))
        jd_text = jd_edu.get('normalized_text') or self.normalize_text(jd_edu.get('raw_text', ''))

        base_similarity = 0.0
        if resume_text and jd_text:
            base_similarity = self.compute_similarity(resume_text, jd_text)

        resume_level = resume_edu.get('degree_level', 'unknown')
        jd_level = jd_edu.get('degree_level', 'unknown')

        resume_rank = self.level_hierarchy.get(resume_level, 0)
        jd_rank = self.level_hierarchy.get(jd_level, 0)

        if jd_rank == 0:
            return min(1.0, base_similarity + 0.15 * resume_rank)

        level_gap = resume_rank - jd_rank
        if level_gap >= 1:
            heuristic_score = 0.9
        elif level_gap == 0:
            heuristic_score = 0.8
        elif level_gap == -1:
            heuristic_score = 0.6
        else:
            heuristic_score = 0.4

        final_score = max(heuristic_score, base_similarity)
        return min(1.0, final_score)
    
    def compute_skills_similarity(self, resume_skills: List[str], jd_skills: List[str]) -> Tuple[float, Dict]:
        if not jd_skills:
            return 1.0, {'matched': [], 'missing': [], 'extra': resume_skills}
        
        if not resume_skills:
            return 0.0, {'matched': [], 'missing': jd_skills, 'extra': []}
        
        resume_skills_set = set([s.lower() for s in resume_skills])
        jd_skills_set = set([s.lower() for s in jd_skills])
        
        matched = list(resume_skills_set & jd_skills_set)
        missing = list(jd_skills_set - resume_skills_set)
        extra = list(resume_skills_set - jd_skills_set)
        
        exact_match_score = len(matched) / len(jd_skills_set) if jd_skills_set else 0
        
        resume_text = ' '.join(resume_skills)
        jd_text = ' '.join(jd_skills)
        semantic_similarity = self.compute_similarity(resume_text, jd_text)
        
        final_score = min(1.0, 0.85 * exact_match_score + 0.15 * semantic_similarity)
        
        breakdown = {
            'matched': matched,
            'missing': missing,
            'extra': extra,
            'match_ratio': f"{len(matched)}/{len(jd_skills_set)}"
        }
        
        return final_score, breakdown
    
    def compute_experience_similarity(self, resume_exp: Dict, jd_exp: Dict) -> float:
        resume_years = resume_exp.get('years', 0) or 0
        jd_years = jd_exp.get('years', 0) or 0

        if jd_years > 0:
            years_score = min(1.0, resume_years / jd_years)
        else:
            years_score = min(1.0, resume_years / max(1.0, resume_years + 2))

        resume_text = resume_exp.get('normalized_text') or resume_exp.get('raw_text', '')
        jd_text = jd_exp.get('normalized_text') or jd_exp.get('raw_text', '')

        if resume_text and jd_text:
            semantic_score = self.compute_similarity(resume_text, jd_text)
        else:
            semantic_score = 0.0

        resume_titles = set(resume_exp.get('job_titles', []))
        jd_titles = set(jd_exp.get('job_titles', []))
        title_overlap = 0.0
        if resume_titles and jd_titles:
            overlap = len(resume_titles & jd_titles)
            title_overlap = min(1.0, overlap / max(1, len(jd_titles)))

        final_score = 0.45 * years_score + 0.35 * semantic_score + 0.2 * title_overlap
        return min(1.0, final_score)
    
    def compute_profession_similarity(self, resume_text: str, jd_text: str) -> float:
        if not resume_text or not jd_text:
            return 0.5
        
        resume_normalized = self.normalize_text(resume_text[:1000])
        jd_normalized = self.normalize_text(jd_text[:1000])
        
        similarity = self.compute_similarity(resume_normalized, jd_normalized)
        return similarity


nlp_service = NLPService()
