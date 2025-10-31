from django.contrib import admin
from .models import User, Profile, Resume, JobDescription, MatchAttempt, AdminSettings, SystemLog


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'role', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    readonly_fields = ['created_at', 'last_login']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'updated_at']
    search_fields = ['user__email', 'summary']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['user', 'source_type', 'filename', 'created_at']
    list_filter = ['source_type', 'created_at']
    search_fields = ['user__email', 'filename']
    readonly_fields = ['created_at']


@admin.register(JobDescription)
class JobDescriptionAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'user__email', 'raw_text']
    readonly_fields = ['created_at']


@admin.register(MatchAttempt)
class MatchAttemptAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'final_score', 'profession_match_flag', 'created_at']
    list_filter = ['profession_match_flag', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['created_at']


@admin.register(AdminSettings)
class AdminSettingsAdmin(admin.ModelAdmin):
    list_display = ['id', 'weight_education', 'weight_skills', 'weight_experience', 'updated_at']
    readonly_fields = ['updated_at']
    
    def has_add_permission(self, request):
        return not AdminSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action_type', 'ip_address', 'created_at']
    list_filter = ['action_type', 'created_at']
    search_fields = ['user__email', 'action_type']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False
