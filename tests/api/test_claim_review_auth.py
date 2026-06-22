"""청구항 심사 Django 프록시의 인증 경계 테스트."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import django

DJANGO_ROOT = Path(__file__).resolve().parents[2] / "backend" / "django"
sys.path.insert(0, str(DJANGO_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from asgiref.sync import async_to_sync
from django.test import RequestFactory

from workspace.views import review_claims_api


def make_request():
    return RequestFactory().post(
        "/workspace/review_claims_api/",
        data=json.dumps({
            "claim_text": "입력 데이터를 분석하여 결과를 제공하는 인공지능 시스템."
        }),
        content_type="application/json",
    )


def test_review_claims_requires_jwt_authentication():
    with patch(
        "rest_framework_simplejwt.authentication.JWTAuthentication.authenticate",
        return_value=None,
    ):
        response = async_to_sync(review_claims_api)(make_request())

    assert response.status_code == 401


def test_review_claims_accepts_authenticated_request():
    with patch(
        "rest_framework_simplejwt.authentication.JWTAuthentication.authenticate",
        return_value=(object(), object()),
    ):
        response = async_to_sync(review_claims_api)(make_request())

    assert response.status_code == 200
    assert response["Content-Type"].startswith("application/x-ndjson")
