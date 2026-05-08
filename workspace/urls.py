# workspace/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),    
    path('create/', views.create_project, name='create_project'),
]