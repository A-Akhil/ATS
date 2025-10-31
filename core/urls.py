from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('auth/register/', views.register_view, name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('onboarding/', views.onboarding, name='onboarding'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('resume/generate/', views.generate_resume, name='generate_resume'),
    path('resume/<int:resume_id>/', views.resume_view, name='resume_view'),
    path('resume/<int:resume_id>/download/', views.resume_download, name='resume_download'),
    path('resume/<int:resume_id>/latex/', views.resume_latex_download, name='resume_latex_download'),
    path('match/', views.match_job, name='match_job'),
    path('match/<int:match_id>/result/', views.match_result, name='match_result'),
    path('admin/panel/', views.admin_panel, name='admin_panel'),
    path('admin/settings/', views.admin_settings, name='admin_settings'),
]
