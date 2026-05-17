# workspace/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),    
    path('create/', views.create_project, name='create_project'),
    path('workstation/<int:project_id>/', views.workstation, name='workstation'),
    path('workstation/<int:project_id>/chat_api/', views.chat_api, name='chat_api'),
    path('mypage/', views.my_page, name='my_page'),
]