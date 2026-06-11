from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'accounts'

urlpatterns = [
    # Landing
    path('', views.landing, name='landing'),

    # Auth
    path('accounts/login/',    views.login_view,  name='login'),
    path('accounts/logout/',   views.logout_view, name='logout'),
    path('accounts/signup/',   views.signup_view, name='signup'),

    # App
    path('accounts/dashboard/', views.dashboard, name='dashboard'),
    path('accounts/pipeline/',  views.pipeline,  name='pipeline'),

    # Info pages
    path('about/',             views.about_view,          name='about'),
    path('features/',          views.features_view,       name='features'),
    path('agents/',            RedirectView.as_view(pattern_name='accounts:features', permanent=False), name='agents_overview'),
    path('team/',              views.team_view,            name='team'),
    path('team/<slug:slug>/',  views.team_member_view,    name='team_member'),
    path('insights/',          views.insights_view,        name='insights'),
    path('qna/',               views.qna_view,             name='qna'),

    # Chat
    path('accounts/chat/',         views.chat_view,   name='chat'),
    path('accounts/chat/stream/',  views.chat_stream, name='chat_stream'),
    path('accounts/chat/upload/',  views.chat_upload, name='chat_upload'),

    # Agent detail pages
    path('agents/summary/',       views.agent_detail, {'slug': 'summary'},       name='agent_summary'),
    path('agents/prior-art/',     views.agent_detail, {'slug': 'prior-art'},     name='agent_prior_art'),
    path('agents/claim/',         views.agent_detail, {'slug': 'claim'},         name='agent_claim'),
    path('agents/drawing/',       views.agent_detail, {'slug': 'drawing'},       name='agent_drawing'),
    path('agents/drawing/gallery/', views.drawing_gallery, name='drawing_gallery'),
    path('agents/specification/', views.agent_detail, {'slug': 'specification'}, name='agent_specification'),
    path('agents/composer/',      views.agent_detail, {'slug': 'composer'},      name='agent_composer'),
]
