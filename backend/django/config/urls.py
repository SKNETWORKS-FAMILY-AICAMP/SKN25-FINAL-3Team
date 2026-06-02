"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.http import JsonResponse

from rest_framework_simplejwt.views import TokenRefreshView
from accounts.api_views import SignupAPIView, LoginAPIView, LogoutAPIView, MeAPIView


def health(request):
    return JsonResponse({"status": "ok", "service": "patent-auth"})


urlpatterns = [
    # ── 헬스체크 ──────────────────────────────────
    path('health/', health, name='health'),

    # ── Django Admin ──────────────────────────────
    path('admin/', admin.site.urls),

    # ── 템플릿 기반 인증 페이지 (브라우저용) ───────
    path('accounts/', include('accounts.urls')),
    path('', lambda request: redirect('accounts:login'), name='home'),

    # ── JWT REST API 엔드포인트 (멀티에이전트 연결용) ─
    path('api/auth/signup/',         SignupAPIView.as_view(),  name='api-signup'),
    path('api/auth/login/',          LoginAPIView.as_view(),   name='api-login'),
    path('api/auth/logout/',         LogoutAPIView.as_view(),  name='api-logout'),
    path('api/auth/token/refresh/',  TokenRefreshView.as_view(), name='api-token-refresh'),
    path('api/auth/me/',             MeAPIView.as_view(),      name='api-me'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
