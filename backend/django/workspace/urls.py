# workspace/urls.py
from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('dashboard/', RedirectView.as_view(url='/accounts/chat/', permanent=False)),
    path('create/', views.create_project, name='create_project'),
    path('workstation/<int:project_id>/', views.workstation, name='workstation'),
    path('workstation/<int:project_id>/chat_api/', views.chat_api, name='chat_api'),
    path('mypage/', views.my_page, name='my_page'),
    path('delete/<int:project_id>/', views.delete_project, name='delete_project'),
    path('workstation/<int:project_id>/upload_api/', views.upload_file_api, name='upload_file_api'),
    path('workstation/<int:project_id>/welcome_api/', views.welcome_api, name='welcome_api'),
    path('workstation/<int:project_id>/generate_claims_api/', views.generate_claims_api, name='generate_claims_api'),
    path('workstation/<int:project_id>/save_claims_api/', views.save_claims_api, name='save_claims_api'),
    path('workstation/<int:project_id>/manage_claims_api/', views.manage_claims_api, name='manage_claims_api'),
    path('workstation/bulk_delete/', views.bulk_delete_projects_api, name='bulk_delete_projects_api'),
    path('workstation/<int:project_id>/report/', views.patent_report_view, name='patent_report'),
]