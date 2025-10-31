from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
from typing import Dict, List, Tuple


class NLPService:
    def __init__(self):
        try:
            print("[NLP] Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            print("[NLP] SentenceTransformer model loaded successfully")
        except Exception as e:
            print(f"[NLP ERROR] Error loading sentence transformer: {e}")
            self.model = None
    
    def normalize_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_education(self, text: str) -> Dict:
        text = self.normalize_text(text)
        
        degree_patterns = {
            'doctoral': r'\b(phd|ph\.d|doctorate|doctoral)\b',
            'master': r'\b(master|m\.?s\.?|m\.?a\.?|m\.?tech|m\.?b\.?a|mba)\b',
            'bachelor': r'\b(bachelor|b\.?s\.?|b\.?a\.?|b\.?tech|b\.?e\.?|b\.?com|btech|bcom)\b',
            'diploma': r'\b(diploma|associate)\b',
        }
        
        degrees = []
        for level, pattern in degree_patterns.items():
            if re.search(pattern, text):
                degrees.append(level)
        
        degree_level = degrees[0] if degrees else 'unknown'
        
        return {
            'degree_level': degree_level,
            'degrees': degrees,
            'raw_text': text
        }
    
    def extract_skills(self, text: str) -> List[str]:
        text = self.normalize_text(text)
        
        common_skills = [
            'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin',
            'react', 'angular', 'vue', 'node', 'express', 'django', 'flask', 'spring',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git',
            'machine learning', 'deep learning', 'nlp', 'computer vision', 'data science',
            'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
            'html', 'css', 'sass', 'bootstrap', 'tailwind',
            'rest api', 'graphql', 'microservices', 'agile', 'scrum', 'devops',
            'leadership', 'communication', 'problem solving', 'teamwork', 'project management'
        ]
        
        found_skills = []
        for skill in common_skills:
            if skill in text:
                found_skills.append(skill)
        
        words = text.split()
        tech_patterns = [
            r'\b[a-z]+\.js\b',
            r'\b[a-z]+sql\b',
            r'\b[a-z]+db\b',
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, text)
            found_skills.extend(matches)
        
        return list(set(found_skills))
    
    def extract_experience(self, text: str) -> Dict:
        text = self.normalize_text(text)
        
        year_pattern = r'\b(\d+)\s*(year|yr)s?\b'
        years_match = re.search(year_pattern, text)
        years = int(years_match.group(1)) if years_match else 0
        
        job_titles = []
        title_patterns = [
            r'\b(software|senior|junior|lead|principal|staff)\s+(engineer|developer|programmer)\b',
            r'\b(data|ml|machine learning)\s+(scientist|engineer|analyst)\b',
            r'\b(project|product|program)\s+manager\b',
            r'\b(frontend|backend|full stack|fullstack)\s+(developer|engineer)\b',
            r'\barchitect\b',
            r'\bconsultant\b',
        ]
        
        for pattern in title_patterns:
            matches = re.findall(pattern, text)
            job_titles.extend([' '.join(match) if isinstance(match, tuple) else match for match in matches])
        
        return {
            'years': years,
            'job_titles': list(set(job_titles)),
            'raw_text': text
        }
    
    def parse_resume_sections(self, text: str) -> Dict:
        print("[NLP] Parsing resume sections...")
        result = {
            'education': self.extract_education(text),
            'skills': self.extract_skills(text),
            'experience': self.extract_experience(text)
        }
        print(f"[NLP] Resume sections parsed - Education: {result['education']['degree_level']}, Skills: {len(result['skills'])}, Experience: {result['experience']['years']} years")
        return result
    
    def parse_jd_sections(self, text: str) -> Dict:
        print("[NLP] Parsing JD sections...")
        result = {
            'education': self.extract_education(text),
            'skills': self.extract_skills(text),
            'experience': self.extract_experience(text)
        }
        print(f"[NLP] JD sections parsed - Education: {result['education']['degree_level']}, Skills: {len(result['skills'])}, Experience: {result['experience']['years']} years")
        return result
    
    def compute_embeddings(self, texts: List[str]) -> np.ndarray:
        if not self.model:
            print("[NLP WARNING] Model not loaded, returning zero embeddings")
            return np.zeros((len(texts), 384))
        print(f"[NLP] Computing embeddings for {len(texts)} text(s)...")
        embeddings = self.model.encode(texts)
        print(f"[NLP] Embeddings computed: shape {embeddings.shape}")
        return embeddings
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0
        
        embeddings = self.compute_embeddings([text1, text2])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(similarity)
    
    def compute_education_similarity(self, resume_edu: Dict, jd_edu: Dict) -> float:
        resume_text = resume_edu.get('raw_text', '')
        jd_text = jd_edu.get('raw_text', '')
        
        if not resume_text or not jd_text:
            return 0.0
        
        base_similarity = self.compute_similarity(resume_text, jd_text)
        
        resume_level = resume_edu.get('degree_level', 'unknown')
        jd_level = jd_edu.get('degree_level', 'unknown')
        
        level_hierarchy = {'doctoral': 4, 'master': 3, 'bachelor': 2, 'diploma': 1, 'unknown': 0}
        
        resume_rank = level_hierarchy.get(resume_level, 0)
        jd_rank = level_hierarchy.get(jd_level, 0)
        
        if resume_rank >= jd_rank:
            level_bonus = 0.1
        elif resume_rank == jd_rank - 1:
            level_bonus = 0.0
        else:
            level_bonus = -0.2
        
        final_score = min(1.0, max(0.0, base_similarity + level_bonus))
        return final_score
    
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
        
        final_score = 0.6 * exact_match_score + 0.4 * semantic_similarity
        
        breakdown = {
            'matched': matched,
            'missing': missing,
            'extra': extra,
            'match_ratio': f"{len(matched)}/{len(jd_skills_set)}"
        }
        
        return min(1.0, final_score), breakdown
    
    def compute_experience_similarity(self, resume_exp: Dict, jd_exp: Dict) -> float:
        resume_years = resume_exp.get('years', 0)
        jd_years = jd_exp.get('years', 0)
        
        if jd_years > 0:
            years_score = min(1.0, resume_years / jd_years)
        else:
            years_score = 0.5
        
        resume_text = resume_exp.get('raw_text', '')
        jd_text = jd_exp.get('raw_text', '')
        
        if resume_text and jd_text:
            semantic_score = self.compute_similarity(resume_text, jd_text)
        else:
            semantic_score = 0.0
        
        final_score = 0.4 * years_score + 0.6 * semantic_score
        return min(1.0, final_score)
    
    def compute_profession_similarity(self, resume_text: str, jd_text: str) -> float:
        if not resume_text or not jd_text:
            return 0.5
        
        resume_normalized = self.normalize_text(resume_text[:1000])
        jd_normalized = self.normalize_text(jd_text[:1000])
        
        similarity = self.compute_similarity(resume_normalized, jd_normalized)
        return similarity


nlp_service = NLPService()
