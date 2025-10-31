import requests
from django.conf import settings
import os


class LaTeXService:
    def __init__(self):
        self.service_url = settings.LATEX_SERVICE_URL
    
    def compile_latex_to_pdf(self, latex_content: str, output_filename: str) -> dict:
        temp_tex_file = f"/tmp/{output_filename}.tex"
        
        try:
            with open(temp_tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            with open(temp_tex_file, 'rb') as f:
                files = {'file': (f'{output_filename}.tex', f, 'text/plain')}
                response = requests.post(self.service_url, files=files, timeout=30)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'pdf_content': response.content,
                    'error': None
                }
            else:
                error_text = response.text if response.text else f"HTTP {response.status_code}"
                return {
                    'success': False,
                    'pdf_content': None,
                    'error': error_text
                }
        
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'pdf_content': None,
                'error': 'LaTeX service not available. Make sure the service is running on localhost:8006'
            }
        except Exception as e:
            return {
                'success': False,
                'pdf_content': None,
                'error': str(e)
            }
        finally:
            if os.path.exists(temp_tex_file):
                os.remove(temp_tex_file)
    
    def get_default_template(self) -> str:
        template_path = os.path.join(settings.BASE_DIR, 'template.tex')
        
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        return self.get_fallback_template()
    
    def get_fallback_template(self) -> str:
        return r"""
\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.75in]{geometry}
\usepackage{enumitem}
\usepackage{hyperref}

\begin{document}

\begin{center}
{\Large \textbf{{{NAME}}}}\\
\vspace{2mm}
{{EMAIL}} | {{PHONE}}\\
\end{center}

\vspace{3mm}

\section*{Professional Summary}
{{SUMMARY}}

\section*{Education}
\begin{itemize}[leftmargin=*]
{{EDUCATION_ENTRIES}}
\end{itemize}

\section*{Skills}
{{SKILLS}}

\section*{Experience}
\begin{itemize}[leftmargin=*]
{{EXPERIENCE_ENTRIES}}
\end{itemize}

\section*{Projects}
\begin{itemize}[leftmargin=*]
{{PROJECTS}}
\end{itemize}

\section*{Certifications}
\begin{itemize}[leftmargin=*]
{{CERTIFICATIONS}}
\end{itemize}

\end{document}
"""


latex_service = LaTeXService()
