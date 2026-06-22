"""Unit tests for the current Django account model and JWT API contract."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import UserProfile


User = get_user_model()

SIGNUP_URL = "/accounts/signup/"
LOGIN_URL = "/accounts/login/"
LOGOUT_URL = "/accounts/logout/"
ME_URL = "/accounts/me/"

VALID_PAYLOAD = {
    "username": "testuser",
    "name": "홍길동",
    "gender": "M",
    "age": 30,
    "password": "strongpass123",
}


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    user = User.objects.create_user(
        username="existing",
        first_name="기존유저",
        email="existing@example.com",
        password="pass1234!",
    )
    UserProfile.objects.create(user=user, gender="F", age=25, role="inventor")
    return user


@pytest.fixture
def auth_client(user):
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client, user, str(token)


def test_standard_user_password_is_hashed(db):
    user = User.objects.create_user(username="u1", password="pw")

    assert user.username == "u1"
    assert user.check_password("pw")
    assert user.is_active is True


def test_user_profile_string_uses_username(user):
    assert str(user.profile) == "existing"


def test_signup_creates_user_profile_and_tokens(client, db):
    response = client.post(SIGNUP_URL, VALID_PAYLOAD, format="json")

    assert response.status_code == 201
    assert {"access", "refresh", "user", "message"}.issubset(response.data)
    created = User.objects.get(username="testuser")
    assert created.first_name == "홍길동"
    assert created.profile.role == "inventor"
    assert created.profile.age == 30


def test_signup_rejects_duplicate_username(client, user):
    response = client.post(
        SIGNUP_URL,
        {**VALID_PAYLOAD, "username": user.username},
        format="json",
    )

    assert response.status_code == 400
    assert "이미 존재" in response.data["error"]


def test_login_returns_tokens_and_serialized_user(client, user):
    response = client.post(
        LOGIN_URL,
        {"username": user.username, "password": "pass1234!"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["user"]["username"] == user.username
    assert response.data["user"]["name"] == "기존유저"
    assert response.data["user"]["gender"] == "F"


def test_login_rejects_wrong_password(client, user):
    response = client.post(
        LOGIN_URL,
        {"username": user.username, "password": "wrong"},
        format="json",
    )

    assert response.status_code == 401


def test_me_requires_authentication(client, db):
    assert client.get(ME_URL).status_code == 401


def test_me_returns_and_updates_current_user(auth_client):
    client, user, _refresh = auth_client

    get_response = client.get(ME_URL)
    patch_response = client.patch(
        ME_URL,
        {"name": "수정이름", "email": "updated@example.com"},
        format="json",
    )

    assert get_response.status_code == 200
    assert get_response.data["user"]["username"] == user.username
    assert patch_response.status_code == 200
    user.refresh_from_db()
    assert user.first_name == "수정이름"
    assert user.email == "updated@example.com"


def test_logout_blacklists_valid_refresh_token(auth_client):
    client, _user, refresh_token = auth_client

    response = client.post(LOGOUT_URL, {"refresh": refresh_token}, format="json")

    assert response.status_code == 200
    assert response.data["message"] == "로그아웃 성공"


def test_logout_rejects_invalid_refresh_token(auth_client):
    client, _user, _refresh_token = auth_client

    response = client.post(LOGOUT_URL, {"refresh": "not-a-token"}, format="json")

    assert response.status_code == 400
