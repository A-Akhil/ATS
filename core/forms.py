from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Profile, JobDescription, AdminSettings
import json


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True, max_length=150)
    last_name = forms.CharField(required=True, max_length=150)
    phone = forms.CharField(required=False, max_length=20)
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'username', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data.get('phone', '')
        
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'autofocus': True}))


class ProfileForm(forms.ModelForm):
    summary = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        help_text='Professional summary or bio'
    )
    
    class Meta:
        model = Profile
        fields = ['summary']


class EducationEntryForm(forms.Form):
    degree = forms.CharField(max_length=100, required=True)
    field = forms.CharField(max_length=100, required=True, label='Field of Study')
    institution = forms.CharField(max_length=200, required=True)
    start_year = forms.IntegerField(required=True, min_value=1950, max_value=2030)
    end_year = forms.IntegerField(required=True, min_value=1950, max_value=2030)
    
    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_year')
        end = cleaned_data.get('end_year')
        
        if start and end and start > end:
            raise forms.ValidationError('Start year must be before end year')
        
        return cleaned_data


class ExperienceEntryForm(forms.Form):
    title = forms.CharField(max_length=100, required=True, label='Job Title')
    company = forms.CharField(max_length=200, required=True)
    start = forms.CharField(max_length=50, required=True, label='Start Date (e.g., Jan 2020)')
    end = forms.CharField(max_length=50, required=True, label='End Date (e.g., Dec 2022 or Present)')
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=True,
        help_text='Describe your responsibilities and achievements'
    )
    tech_stack = forms.CharField(
        max_length=500,
        required=False,
        help_text='Technologies used (comma-separated)'
    )


class SkillsForm(forms.Form):
    skills = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=True,
        help_text='Enter skills separated by commas (e.g., Python, Django, React)'
    )
    
    def clean_skills(self):
        skills_text = self.cleaned_data['skills']
        skills_list = [s.strip() for s in skills_text.split(',') if s.strip()]
        return skills_list


class ProjectForm(forms.Form):
    name = forms.CharField(max_length=200, required=True)
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=True
    )
    technologies = forms.CharField(
        max_length=500,
        required=False,
        help_text='Technologies used (comma-separated)'
    )
    url = forms.URLField(required=False, help_text='Project URL or GitHub link')


class CertificationForm(forms.Form):
    name = forms.CharField(max_length=200, required=True)
    issuer = forms.CharField(max_length=200, required=True, label='Issued By')
    date = forms.CharField(max_length=50, required=True, label='Issue Date')
    credential_id = forms.CharField(max_length=100, required=False, label='Credential ID')


class JobDescriptionForm(forms.ModelForm):
    title = forms.CharField(max_length=255, required=True, label='Job Title')
    raw_text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 15, 'placeholder': 'Paste the job description here...'}),
        required=True,
        label='Job Description'
    )
    
    class Meta:
        model = JobDescription
        fields = ['title', 'raw_text']


class ResumeUploadForm(forms.Form):
    resume_file = forms.FileField(
        required=True,
        help_text='Upload PDF resume',
        widget=forms.FileInput(attrs={'accept': '.pdf'})
    )
    
    def clean_resume_file(self):
        file = self.cleaned_data['resume_file']
        if file:
            if not file.name.endswith('.pdf'):
                raise forms.ValidationError('Only PDF files are allowed')
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size must be under 5MB')
        return file


class AdminSettingsForm(forms.ModelForm):
    class Meta:
        model = AdminSettings
        fields = [
            'weight_education',
            'weight_skills',
            'weight_experience',
            'profession_zero_threshold',
            'profession_cap_threshold',
            'partial_credit_cap'
        ]
        widgets = {
            'weight_education': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '1', 'class': 'w-full rounded-xl border border-gray-200 px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
            'weight_skills': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '1', 'class': 'w-full rounded-xl border border-gray-200 px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
            'weight_experience': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '1', 'class': 'w-full rounded-xl border border-gray-200 px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
            'profession_zero_threshold': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '1', 'class': 'w-full rounded-xl border border-gray-200 px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
            'profession_cap_threshold': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '1', 'class': 'w-full rounded-xl border border-gray-200 px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
            'partial_credit_cap': forms.NumberInput(attrs={'step': '1', 'min': '0', 'max': '100', 'class': 'w-full rounded-xl border border-gray-200 px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        weight_sum = (
            cleaned_data.get('weight_education', 0) +
            cleaned_data.get('weight_skills', 0) +
            cleaned_data.get('weight_experience', 0)
        )
        
        if abs(weight_sum - 1.0) > 0.01:
            raise forms.ValidationError(
                f'Weights must sum to 1.0 (currently {weight_sum:.2f})'
            )
        
        return cleaned_data
