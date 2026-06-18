# accounts/urls.py (혹은 앱 폴더의 urls.py)
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # auth.ts의 엔드포인트들과 정확히 맵핑
    path('signup/', views.signup_api, name='signup'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', views.logout_api, name='logout'),
    path('me/', views.me_api, name='me'),
    
    # client.ts의 tryRefresh() 함수에서 호출하는 토큰 갱신 주소
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]