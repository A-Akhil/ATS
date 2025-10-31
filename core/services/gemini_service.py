from google import genai
from google.genai import types
from django.conf import settings
import json
import re


class GeminiService:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        else:
            self.client = None
    
    def generate_latex_resume(self, profile_data, template_content):
        if not self.client:
            return {"error": "Gemini API key not configured"}
        
        prompt = f"""
You are a LaTeX resume generator. Fill the following LaTeX template with the user profile data.
Ensure the output is ATS-friendly with clean headings, bullet lists, and no fancy visuals.
Keep every section heading exactly as it appears in the LaTeX template (do not rename or embellish headings such as changing "Projects" to "Selected Projects").
Only populate or remove sections as indicated by the template and provided data; never introduce new sections or modify section titles.

User Profile Data:
{json.dumps(profile_data, indent=2)}

LaTeX Template:
{template_content}

IMPORTANT: Return ONLY valid LaTeX code. Do not include any markdown code blocks, explanations, or additional text.
Start directly with \\documentclass and end with \\end{{document}}.
Make sure all special characters are properly escaped for LaTeX.
"""
        
        try:
            response = self.client.models.generate_content(
                model='gemini-flash-latest',
                contents=prompt
            )
            latex_code = response.text.strip()
            
            latex_code = re.sub(r'^```latex\s*', '', latex_code)
            latex_code = re.sub(r'^```\s*', '', latex_code)
            latex_code = re.sub(r'\s*```$', '', latex_code)
            latex_code = latex_code.strip()
            
            return {
                "success": True,
                "latex": latex_code
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_match_scores(self, resume_sections, jd_sections, bert_scores, profession_similarity):
        print("[GEMINI] Validating match scores...")
        if not self.client:
            print("[GEMINI WARNING] API client not configured")
            return None
        
        prompt = f"""
You are an expert ATS (Applicant Tracking System) validator. 
Review the following BERT-based scores for a resume-job match and provide your assessment.

Resume Sections:
- Education: {json.dumps(resume_sections.get('education', {}), indent=2)}
- Skills: {json.dumps(resume_sections.get('skills', []), indent=2)}
- Experience: {json.dumps(resume_sections.get('experience', []), indent=2)}

Job Requirements:
- Education Required: {json.dumps(jd_sections.get('education', {}), indent=2)}
- Skills Required: {json.dumps(jd_sections.get('skills', []), indent=2)}
- Experience Required: {json.dumps(jd_sections.get('experience', {}), indent=2)}

BERT Scores (0-1 scale):
- Education Score: {bert_scores.get('education', 0)}
- Skills Score: {bert_scores.get('skills', 0)}
- Experience Score: {bert_scores.get('experience', 0)}
- Profession Similarity: {profession_similarity}

Please provide:
1. Corrected scores (0-1 scale) if you disagree with BERT (do not mention these scores in your written guidance)
2. Whether the profession truly mismatches (boolean) and a brief rationale when true
3. A concise resume review (2-3 sentences) explaining how the candidate can improve against this job description; avoid any mention of underlying model names or BERT scores
4. One short actionable tip the candidate can implement immediately
5. Final recommended score (0-100 scale)

Return your response ONLY as a valid JSON object with this exact structure:
{{
    "education_score": <float 0-1>,
    "skills_score": <float 0-1>,
    "experience_score": <float 0-1>,
    "final_score": <float 0-100>,
    "profession_mismatch": <true | false>,
    "profession_reason": "<brief explanation if profession_mismatch is true, otherwise note alignment>",
    "review": "<2-3 sentence improvement guidance without referencing BERT>",
    "suggestion": "<one-sentence actionable tip>",
    "reason": "<brief explanation of score adjustments>"
}}
"""
        
        try:
            print("[GEMINI] Sending validation request to Gemini API...")
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.2
                )
            )
            print("[GEMINI] Response received from Gemini API")
            response_text = response.text.strip()
            
            response_text = re.sub(r'^```json\s*', '', response_text)
            response_text = re.sub(r'^```\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
            response_text = response_text.strip()
            
            print(f"[GEMINI] Parsing JSON response...")
            correction_data = json.loads(response_text)
            print(f"[GEMINI] Validation complete - Final score: {correction_data.get('final_score')}")
            return correction_data
        except Exception as e:
            print(f"[GEMINI ERROR] Validation error: {e}")
            return None
    
    def detect_profession(self, text):
        if not self.client:
            return {"domain": "Other", "confidence": 0.5}
        
        prompt = f"""
Analyze the following text and determine the most likely profession domain.

Text:
{text[:2000]}

Choose from: Software, Data Science, Healthcare, Finance, Legal, Education, Marketing, Sales, Operations, Other

Return ONLY a valid JSON object:
{{
  "domain": "<domain name>",
  "confidence": <float 0-1>
}}
"""
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.2
                )
            )
            response_text = response.text.strip()
            
            response_text = re.sub(r'^```json\s*', '', response_text)
            response_text = re.sub(r'^```\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            return result
        except Exception as e:
            print(f"Profession detection error: {e}")
            return {"domain": "Other", "confidence": 0.5}


gemini_service = GeminiService()
