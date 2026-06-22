# accounts/urls.py (혹은 앱 폴더의 urls.py)
from django.urls import path
from django.views.generic import RedirectView
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    # auth.ts의 엔드포인트들과 정확히 맵핑
    path('signup/', views.signup_api, name='signup'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', views.logout_api, name='logout'),
    path('me/', views.me_api, name='me'),

    # client.ts의 tryRefresh() 함수에서 호출하는 토큰 갱신 주소
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

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
]
