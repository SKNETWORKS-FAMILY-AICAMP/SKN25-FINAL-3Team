from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('about/', views.about, name='about'),
    path('features/', views.features, name='features'),
    path('team/', views.team, name='team'),
    path('agents/', views.agents_overview, name='agents_overview'),
    path('agents/<slug:slug>/', views.agent_detail, name='agent_detail'),
    path('drawing-gallery/', views.drawing_gallery, name='drawing_gallery'),
    path('insights/', views.insights, name='insights'),
    path('qna/', views.qna, name='qna'),
    # alias redirects used by page templates
    path('landing/', RedirectView.as_view(url='/', permanent=False), name='landing'),
    path('chat/', RedirectView.as_view(pattern_name='dashboard', permanent=False), name='chat'),
    path('pipeline/', RedirectView.as_view(pattern_name='create_project', permanent=False), name='pipeline'),
    path('login/', RedirectView.as_view(url='/accounts/login/', permanent=False), name='login'),
]
