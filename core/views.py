from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, FileResponse
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.db.models import Q
import json
from datetime import datetime
import PyPDF2
import io

from .models import User, Profile, Resume, JobDescription, MatchAttempt, AdminSettings, SystemLog
from .forms import (
    RegisterForm, LoginForm, ProfileForm, JobDescriptionForm, 
    ResumeUploadForm, AdminSettingsForm
)
from .services.gemini_service import gemini_service
from .services.latex_service import latex_service
from .services.nlp_service import nlp_service
from .services.scoring_service import scoring_service


def log_action(user, action_type, data=None, request=None):
    ip_address = None
    user_agent = None
    
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    SystemLog.objects.create(
        user=user,
        action_type=action_type,
        raw_data=data or {},
        ip_address=ip_address,
        user_agent=user_agent
    )


def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            if settings.STORE_PLAIN_PASSWORD:
                user.plain_password = request.POST.get('password1')
                user.save()
            
            Profile.objects.create(user=user)
            
            log_action(user, 'register', {'email': user.email}, request)
            
            login(request, user)
            messages.success(request, 'Registration successful! Please complete your profile.')
            return redirect('onboarding')
    else:
        form = RegisterForm()
    
    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
        except User.DoesNotExist:
            user = None
        
        if user is not None:
            login(request, user)
            log_action(user, 'login', {}, request)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password')
    
    form = LoginForm()
    return render(request, 'auth/login.html', {'form': form})


@login_required
def logout_view(request):
    log_action(request.user, 'logout', {}, request)
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('landing')


@login_required
def onboarding(request):
    profile = request.user.profile
    
    if request.method == 'POST':
        # Contact Information
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        if full_name:
            name_parts = full_name.split(' ', 1)
            request.user.first_name = name_parts[0]
            request.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        request.user.phone = phone
        request.user.save()

        profile.phone = phone
        profile.city = request.POST.get('city', '').strip()
        profile.state = request.POST.get('state', '').strip()
        profile.linkedin = request.POST.get('linkedin', '').strip()
        profile.github = request.POST.get('github', '').strip()
        
        # Professional Summary
        profile.summary = request.POST.get('summary', '')
        
        # Skills
        skills_raw = request.POST.get('skills', '')
        profile.skills = [s.strip() for s in skills_raw.split(',') if s.strip()]
        
        # Education
        education_entries = []
        edu_count = int(request.POST.get('education_count', 0))
        for i in range(edu_count):
            degree = request.POST.get(f'degree_{i}')
            if degree:
                education_entries.append({
                    'degree': degree,
                    'field': request.POST.get(f'field_{i}', ''),
                    'institution': request.POST.get(f'institution_{i}', ''),
                    'start_year': request.POST.get(f'start_year_{i}', ''),
                    'end_year': request.POST.get(f'end_year_{i}', ''),
                    'gpa': request.POST.get(f'gpa_{i}', ''),
                })
        profile.education_entries = education_entries
        
        # Work Experience
        experiences = []
        exp_count = int(request.POST.get('experience_count', 0))
        for i in range(exp_count):
            title = request.POST.get(f'exp_title_{i}')
            if title:
                description = request.POST.get(f'exp_description_{i}', '')
                responsibilities = [r.strip() for r in description.split('\n') if r.strip()]
                experiences.append({
                    'title': title,
                    'company': request.POST.get(f'exp_company_{i}', ''),
                    'start_date': request.POST.get(f'exp_start_{i}', ''),
                    'end_date': request.POST.get(f'exp_end_{i}', ''),
                    'responsibilities': responsibilities,
                    'description': description,
                })
        profile.experiences = experiences
        
        # Projects
        projects = []
        project_count = int(request.POST.get('project_count', 0))
        for i in range(project_count):
            name = request.POST.get(f'project_name_{i}')
            if name:
                tech_raw = request.POST.get(f'project_tech_{i}', '')
                technologies = [t.strip() for t in tech_raw.split(',') if t.strip()]
                projects.append({
                    'name': name,
                    'description': request.POST.get(f'project_description_{i}', ''),
                    'technologies': technologies,
                    'link': request.POST.get(f'project_link_{i}', ''),
                })
        profile.projects = projects
        
        # Certifications
        certifications = []
        cert_count = int(request.POST.get('certification_count', 0))
        for i in range(cert_count):
            name = request.POST.get(f'cert_name_{i}')
            if name:
                certifications.append({
                    'name': name,
                    'issuer': request.POST.get(f'cert_issuer_{i}', ''),
                    'year': request.POST.get(f'cert_year_{i}', ''),
                })
        profile.certifications = certifications
        
        # Publications (optional)
        publications = []
        pub_count = int(request.POST.get('publication_count', 0))
        for i in range(pub_count):
            title = request.POST.get(f'publication_title_{i}')
            if title:
                publications.append({
                    'title': title,
                    'venue': request.POST.get(f'publication_venue_{i}', ''),
                    'date': request.POST.get(f'publication_date_{i}', ''),
                    'description': request.POST.get(f'publication_description_{i}', ''),
                    'link': request.POST.get(f'publication_link_{i}', ''),
                })
        profile.publications = publications
        
        # Achievements (optional)
        achievements = []
        achievement_count = int(request.POST.get('achievement_count', 0))
        for i in range(achievement_count):
            name = request.POST.get(f'achievement_name_{i}')
            if name:
                achievements.append({
                    'name': name,
                    'organization': request.POST.get(f'achievement_org_{i}', ''),
                    'level': request.POST.get(f'achievement_level_{i}', ''),
                })
        profile.achievements = achievements
        
        # Leadership (optional)
        leadership = []
        leadership_count = int(request.POST.get('leadership_count', 0))
        for i in range(leadership_count):
            role = request.POST.get(f'leadership_role_{i}')
            if role:
                leadership.append({
                    'role': role,
                    'organization': request.POST.get(f'leadership_org_{i}', ''),
                    'location': request.POST.get(f'leadership_location_{i}', ''),
                    'description': request.POST.get(f'leadership_description_{i}', ''),
                })
        profile.leadership = leadership
        
        profile.update_searchable_text()
        profile.save()
        
        log_action(request.user, 'profile_update', {'completed_onboarding': True}, request)
        
        messages.success(request, 'Profile saved successfully!')
        return redirect('dashboard')
    
    return render(request, 'profile/onboarding.html', {'profile': profile})


@login_required
def dashboard(request):
    profile = request.user.profile
    resumes = request.user.resumes.all()[:5]
    recent_matches = request.user.match_attempts.all()[:5]
    
    context = {
        'profile': profile,
        'resumes': resumes,
        'recent_matches': recent_matches,
        'total_matches': request.user.match_attempts.count(),
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def profile_view(request):
    profile = request.user.profile
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_summary':
            profile.summary = request.POST.get('summary', '')
            profile.save()
            messages.success(request, 'Summary updated')
        
        elif action == 'update_skills':
            skills_raw = request.POST.get('skills', '')
            profile.skills = [s.strip() for s in skills_raw.split(',') if s.strip()]
            profile.update_searchable_text()
            profile.save()
            messages.success(request, 'Skills updated')
        
        elif action == 'add_education':
            edu_entry = {
                'degree': request.POST.get('degree'),
                'field': request.POST.get('field'),
                'institution': request.POST.get('institution'),
                'start_year': request.POST.get('start_year'),
                'end_year': request.POST.get('end_year'),
            }
            profile.education_entries.append(edu_entry)
            profile.update_searchable_text()
            profile.save()
            messages.success(request, 'Education added')
        
        elif action == 'add_experience':
            exp_entry = {
                'title': request.POST.get('title'),
                'company': request.POST.get('company'),
                'start': request.POST.get('start'),
                'end': request.POST.get('end'),
                'description': request.POST.get('description'),
                'tech_stack': request.POST.get('tech_stack'),
            }
            profile.experiences.append(exp_entry)
            profile.update_searchable_text()
            profile.save()
            messages.success(request, 'Experience added')
        
        elif action == 'add_project':
            project_entry = {
                'name': request.POST.get('name'),
                'description': request.POST.get('description'),
                'technologies': request.POST.get('technologies'),
                'url': request.POST.get('url'),
            }
            profile.projects.append(project_entry)
            profile.save()
            messages.success(request, 'Project added')
        
        elif action == 'add_certification':
            cert_entry = {
                'name': request.POST.get('name'),
                'issuer': request.POST.get('issuer'),
                'date': request.POST.get('date'),
                'credential_id': request.POST.get('credential_id'),
            }
            profile.certifications.append(cert_entry)
            profile.save()
            messages.success(request, 'Certification added')
        
        log_action(request.user, 'profile_update', {'action': action}, request)
        return redirect('profile')
    
    return render(request, 'profile/profile.html', {'profile': profile})


@login_required
def generate_resume(request):
    profile = request.user.profile
    
    if request.method == 'POST':
        profile_data = {
            'name': f"{request.user.first_name} {request.user.last_name}",
            'email': request.user.email,
            'phone': request.user.phone or '',
            'location': ', '.join(filter(None, [profile.city, profile.state])) or profile.city or '',
            'city': profile.city,
            'state': profile.state,
            'linkedin': profile.linkedin,
            'github': profile.github,
            'summary': profile.summary or '',
            'education': profile.education_entries,
            'skills': profile.skills,
            'experiences': profile.experiences,
            'projects': profile.projects,
            'certifications': profile.certifications,
            'publications': profile.publications,
            'achievements': profile.achievements,
            'leadership': profile.leadership,
        }
        
        template_content = latex_service.get_default_template()
        
        result = gemini_service.generate_latex_resume(profile_data, template_content)
        
        if result.get('success'):
            latex_code = result['latex']
            
            resume = Resume.objects.create(
                user=request.user,
                source_type='generated',
                latex_source=latex_code,
                filename=f'resume_{request.user.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            )
            
            pdf_result = latex_service.compile_latex_to_pdf(
                latex_code, 
                f'resume_{resume.id}'
            )
            
            if pdf_result['success']:
                pdf_path = f'resumes/resume_{resume.id}.pdf'
                from django.core.files.base import ContentFile
                resume.pdf_file.save(pdf_path, ContentFile(pdf_result['pdf_content']))
                resume.save()
                
                log_action(request.user, 'generate_resume', {'resume_id': resume.id}, request)
                messages.success(request, 'Resume generated successfully!')
                return redirect('resume_view', resume_id=resume.id)
            else:
                resume.latex_error = pdf_result['error']
                resume.save()
                messages.warning(request, f'LaTeX generated but PDF compilation failed: {pdf_result["error"]}')
                return redirect('resume_view', resume_id=resume.id)
        else:
            messages.error(request, f'Failed to generate resume: {result.get("error")}')
    
    resumes = Resume.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'resume/generate.html', {'profile': profile, 'resumes': resumes})


@login_required
def resume_view(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    return render(request, 'resume/view.html', {'resume': resume})


@login_required
def resume_download(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    
    if resume.pdf_file:
        response = FileResponse(resume.pdf_file.open('rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{resume.filename}.pdf"'
        return response
    else:
        messages.error(request, 'PDF not available')
        return redirect('resume_view', resume_id=resume_id)


@login_required
def resume_latex_download(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    
    if resume.latex_source:
        response = HttpResponse(resume.latex_source, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{resume.filename}.tex"'
        return response
    else:
        messages.error(request, 'LaTeX source not available')
        return redirect('resume_view', resume_id=resume_id)


@login_required
def match_job(request):
    print(f"[MATCH VIEW] {request.method} request to /match/ by {request.user.email}")
    profile = request.user.profile
    resumes = request.user.resumes.order_by('-created_at')
    resumes_count = resumes.count()
    recent_matches = request.user.match_attempts.all()[:5]
    total_matches = request.user.match_attempts.count()
    print(f"[MATCH VIEW] Resumes available: {resumes_count}")
    
    if request.method == 'POST':
        print(f"[MATCH POST] Keys received: {list(request.POST.keys())}")
        resume_id = request.POST.get('resume_id')
        jd_title = request.POST.get('jd_title') or request.POST.get('job_title') or 'Untitled Position'
        jd_text = request.POST.get('jd_text') or request.POST.get('job_description') or ''
        job_url = request.POST.get('job_url', '').strip()
        company = request.POST.get('company', '').strip()
        
        if not resume_id:
            messages.error(request, 'Please select a resume to match against.')
            print('[MATCH POST] Missing resume_id; redirecting back to form')
            return redirect('match_job')
        
        if not jd_text:
            messages.error(request, 'Provide a job description (pasted text) before analyzing. URL scraping is not yet implemented.')
            print('[MATCH POST] Missing job description text; redirecting back to form')
            return redirect('match_job')
        
        print(f"[MATCH START] Resume ID: {resume_id}, JD Title: {jd_title}, Company: {company}")
        if job_url:
            print(f"[MATCH POST] Job URL provided: {job_url} (currently unused)")
        
        resume = get_object_or_404(Resume, id=resume_id, user=request.user)
        print(f"[MATCH] Resume found: {resume.filename}")
        
        jd = JobDescription.objects.create(
            user=request.user,
            title=jd_title,
            raw_text=jd_text
        )
        print(f"[MATCH] JobDescription created: {jd.id}")
        
        print("[MATCH] Parsing JD sections...")
        jd_sections = nlp_service.parse_jd_sections(jd_text)
        if company:
            jd_sections['company'] = company
        jd.parsed_sections = jd_sections
        jd.save()
        print(f"[MATCH] JD sections parsed: {list(jd_sections.keys())}")
        
        resume_text = resume.parsed_text if resume.parsed_text else resume.latex_source or ''
        
        if not resume.parsed_sections:
            print("[MATCH] Parsing resume sections...")
            resume.parsed_sections = nlp_service.parse_resume_sections(resume_text)
            resume.save()
            print(f"[MATCH] Resume sections parsed: {list(resume.parsed_sections.keys())}")
        
        print("[MATCH] Computing match score (this may take a while)...")
        match_result = scoring_service.compute_match_score(
            resume_text,
            jd_text,
            resume.parsed_sections,
            jd_sections
        )
        print(f"[MATCH] Match score computed: {match_result['final_score']}")
        
        match = MatchAttempt.objects.create(
            user=request.user,
            resume=resume,
            job_description=jd,
            bert_scores=match_result['bert_scores'],
            gemini_correction=match_result.get('gemini_correction'),
            final_score=match_result['final_score'],
            breakdown_details=match_result['breakdown_details'],
            suggestion_text=match_result['suggestion_text'],
            profession_match_flag=match_result['profession_match_flag'],
            profession_similarity=match_result['profession_similarity']
        )
        print(f"[MATCH COMPLETE] MatchAttempt created: {match.id}")
        
        log_action(request.user, 'match', {'match_id': match.id, 'score': match.final_score}, request)
        
        messages.success(request, 'Match analysis completed!')
        return redirect('match_result', match_id=match.id)
    
    print("[MATCH VIEW] Rendering match input page")
    context = {
        'profile': profile,
        'resumes': resumes,
        'recent_matches': recent_matches,
        'total_matches': total_matches,
    }
    return render(request, 'match/match.html', context)


@login_required
def match_result(request, match_id):
    match = get_object_or_404(MatchAttempt, id=match_id, user=request.user)
    return render(request, 'match/result.html', {'match': match})


@login_required
def admin_panel(request):
    if request.user.role != 'admin':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    users = User.objects.all().order_by('-created_at')
    matches = MatchAttempt.objects.all().order_by('-created_at')[:50]
    logs = SystemLog.objects.all().order_by('-created_at')[:100]
    settings_obj = AdminSettings.get_settings()
    
    context = {
        'users': users,
        'matches': matches,
        'logs': logs,
        'settings': settings_obj,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
def admin_settings(request):
    if request.user.role != 'admin':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    settings_obj = AdminSettings.get_settings()
    
    if request.method == 'POST':
        form = AdminSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            log_action(request.user, 'admin_update', {'action': 'settings_update'}, request)
            messages.success(request, 'Settings updated successfully')
            return redirect('admin_settings')
    else:
        form = AdminSettingsForm(instance=settings_obj)
    
    return render(request, 'admin_panel/settings.html', {'form': form, 'settings': settings_obj})
