"""Unit tests for the Django claim-review proxy authentication boundary."""

import json
from unittest.mock import patch

from asgiref.sync import async_to_sync
from django.test import RequestFactory

from workspace.views import review_claims_api


def make_request(body=None):
    payload = body if body is not None else {
        "claim_text": "입력 데이터를 분석하여 결과를 제공하는 인공지능 시스템."
    }
    return RequestFactory().post(
        "/workspace/review_claims_api/",
        data=json.dumps(payload),
        content_type="application/json",
    )


def test_review_claims_requires_jwt_authentication():
    with patch(
        "rest_framework_simplejwt.authentication.JWTAuthentication.authenticate",
        return_value=None,
    ):
        response = async_to_sync(review_claims_api)(make_request())

    assert response.status_code == 401


def test_review_claims_rejects_missing_claim_text_after_authentication():
    with patch(
        "rest_framework_simplejwt.authentication.JWTAuthentication.authenticate",
        return_value=(object(), object()),
    ):
        response = async_to_sync(review_claims_api)(make_request({}))

    assert response.status_code == 400
    assert json.loads(response.content)["error"] == "Claim text is required"


def test_review_claims_accepts_authenticated_request():
    with patch(
        "rest_framework_simplejwt.authentication.JWTAuthentication.authenticate",
        return_value=(object(), object()),
    ):
        response = async_to_sync(review_claims_api)(make_request())

    assert response.status_code == 200
    assert response["Content-Type"].startswith("application/x-ndjson")
    assert response["X-Accel-Buffering"] == "no"
