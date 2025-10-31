from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ]
    
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    plain_password = models.CharField(max_length=255, blank=True, null=True, 
                                     help_text='DEV ONLY - Insecure, for demo purposes only')
    last_login = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    linkedin = models.URLField(blank=True, default='')
    github = models.URLField(blank=True, default='')
    summary = models.TextField(blank=True, null=True, help_text='Professional summary/bio')
    education_entries = models.JSONField(default=list, blank=True, 
                                        help_text='List of education entries')
    skills = models.JSONField(default=list, blank=True, 
                             help_text='List of skills')
    experiences = models.JSONField(default=list, blank=True, 
                                  help_text='List of work experiences')
    certifications = models.JSONField(default=list, blank=True, 
                                     help_text='List of certifications')
    projects = models.JSONField(default=list, blank=True, 
                               help_text='List of projects')
    publications = models.JSONField(default=list, blank=True, 
                                   help_text='List of publications')
    achievements = models.JSONField(default=list, blank=True, 
                                   help_text='List of achievements and awards')
    leadership = models.JSONField(default=list, blank=True, 
                                 help_text='List of leadership or extracurricular roles')
    parsed_searchable_text = models.TextField(blank=True, null=True, 
                                             help_text='Concatenated normalized text')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile of {self.user.email}"
    
    def update_searchable_text(self):
        text_parts = []
        if self.summary:
            text_parts.append(self.summary.lower())
        
        for edu in self.education_entries:
            text_parts.append(f"{edu.get('degree', '')} {edu.get('field', '')} {edu.get('institution', '')}".lower())
        
        text_parts.extend([skill.lower() for skill in self.skills])
        
        for exp in self.experiences:
            responsibilities = ' '.join(exp.get('responsibilities', []))
            description = exp.get('description', '')
            text_parts.append(
                f"{exp.get('title', '')} {exp.get('company', '')} {description} {responsibilities}".lower()
            )
        
        self.parsed_searchable_text = ' '.join(text_parts)
        self.save()


class Resume(models.Model):
    SOURCE_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('generated', 'Generated'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    filename = models.CharField(max_length=255, blank=True, null=True)
    source_type = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    latex_source = models.TextField(blank=True, null=True, help_text='LaTeX source code')
    pdf_file = models.FileField(upload_to='resumes/', blank=True, null=True)
    parsed_text = models.TextField(blank=True, null=True, help_text='Extracted raw text')
    parsed_sections = models.JSONField(default=dict, blank=True, 
                                      help_text='Parsed education, skills, experience')
    latex_error = models.TextField(blank=True, null=True, help_text='LaTeX compilation errors')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Resume of {self.user.email} ({self.source_type})"
    
    class Meta:
        ordering = ['-created_at']


class JobDescription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_descriptions')
    title = models.CharField(max_length=255)
    raw_text = models.TextField(help_text='Job description text')
    parsed_sections = models.JSONField(default=dict, blank=True, 
                                      help_text='Parsed requirements, skills, etc.')
    requirements = models.JSONField(default=list, blank=True, 
                                   help_text='Deduced requirements list')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} by {self.user.email}"
    
    class Meta:
        ordering = ['-created_at']


class MatchAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='match_attempts')
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='matches')
    job_description = models.ForeignKey(JobDescription, on_delete=models.CASCADE, 
                                       related_name='matches')
    
    bert_scores = models.JSONField(default=dict, 
                                  help_text='BERT scores: education, skills, experience, final')
    gemini_correction = models.JSONField(default=dict, blank=True, null=True, 
                                        help_text='Gemini validation and corrections')
    final_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)],
                                   help_text='Final ATS score after corrections')
    breakdown_details = models.JSONField(default=dict, 
                                        help_text='Matched/missing skills, gaps, etc.')
    suggestion_text = models.TextField(blank=True, null=True, 
                                      help_text='Gemini improvement suggestions')
    profession_match_flag = models.BooleanField(default=True, 
                                               help_text='Whether profession matches')
    profession_similarity = models.FloatField(default=1.0, 
                                             validators=[MinValueValidator(0), MaxValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Match {self.id} - Score: {self.final_score}%"
    
    class Meta:
        ordering = ['-created_at']


class AdminSettings(models.Model):
    weight_education = models.FloatField(default=0.35, 
                                        validators=[MinValueValidator(0), MaxValueValidator(1)],
                                        help_text='Weight for education score')
    weight_skills = models.FloatField(default=0.45, 
                                     validators=[MinValueValidator(0), MaxValueValidator(1)],
                                     help_text='Weight for skills score')
    weight_experience = models.FloatField(default=0.20, 
                                         validators=[MinValueValidator(0), MaxValueValidator(1)],
                                         help_text='Weight for experience score')
    
    profession_zero_threshold = models.FloatField(default=0.2, 
                                                 validators=[MinValueValidator(0), MaxValueValidator(1)],
                                                 help_text='Below this: score = 0')
    profession_cap_threshold = models.FloatField(default=0.4, 
                                                validators=[MinValueValidator(0), MaxValueValidator(1)],
                                                help_text='Below this: cap score')
    partial_credit_cap = models.FloatField(default=30.0, 
                                          validators=[MinValueValidator(0), MaxValueValidator(100)],
                                          help_text='Score cap for transferable skills')
    
    allowed_degree_equivalences = models.JSONField(default=dict, blank=True,
                                                   help_text='Degree mapping/equivalences')
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Admin Settings (updated: {self.updated_at})"
    
    def save(self, *args, **kwargs):
        if not self.pk and AdminSettings.objects.exists():
            raise ValueError('Only one AdminSettings instance is allowed (singleton)')
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        settings, _ = cls.objects.get_or_create(id=1)
        return settings
    
    class Meta:
        verbose_name = 'Admin Settings'
        verbose_name_plural = 'Admin Settings'


class SystemLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('register', 'Register'),
        ('generate_resume', 'Generate Resume'),
        ('upload_resume', 'Upload Resume'),
        ('match', 'Match Attempt'),
        ('admin_update', 'Admin Update'),
        ('profile_update', 'Profile Update'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                            related_name='system_logs')
    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES)
    raw_data = models.JSONField(default=dict, blank=True, 
                               help_text='Snapshot of action data')
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        user_str = self.user.email if self.user else 'Anonymous'
        return f"{self.action_type} by {user_str} at {self.created_at}"
    
    class Meta:
        ordering = ['-created_at']
