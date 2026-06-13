import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

SIGNUP_URL = "/api/auth/signup/"
LOGIN_URL = "/api/auth/login/"
LOGOUT_URL = "/api/auth/logout/"
ME_URL = "/api/auth/me/"

VALID_PAYLOAD = {
    "username": "testuser",
    "name": "홍길동",
    "gender": "M",
    "age": 30,
    "password": "strongpass123",
    "password2": "strongpass123",
}


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="existing",
        name="기존유저",
        gender="F",
        age=25,
        password="pass1234!",
    )


@pytest.fixture
def auth_client(user):
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client, user, str(token)


# ── 모델 ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_create_user():
    user = User.objects.create_user(username="u1", name="유저", gender="M", age=20, password="pw")
    assert user.username == "u1"
    assert user.check_password("pw")
    assert user.is_active is True
    assert user.is_staff is False


@pytest.mark.django_db
def test_user_str():
    user = User.objects.create_user(username="u2", name="테스터", gender="F", age=22, password="pw")
    assert str(user) == "테스터 (u2)"


@pytest.mark.django_db
def test_create_user_without_username_raises():
    with pytest.raises(ValueError, match="아이디"):
        User.objects.create_user(username="", name="이름", gender="M", age=20, password="pw")


# ── 회원가입 API ────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_signup_success(client):
    res = client.post(SIGNUP_URL, VALID_PAYLOAD, format="json")
    assert res.status_code == 201
    assert "access" in res.data
    assert res.data["user"]["username"] == "testuser"


@pytest.mark.django_db
def test_signup_duplicate_username(client, user):
    payload = {**VALID_PAYLOAD, "username": user.username}
    res = client.post(SIGNUP_URL, payload, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_signup_password_mismatch(client):
    payload = {**VALID_PAYLOAD, "password2": "different"}
    res = client.post(SIGNUP_URL, payload, format="json")
    assert res.status_code == 400


# ── 로그인 API ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_login_success(client, user):
    res = client.post(LOGIN_URL, {"username": user.username, "password": "pass1234!"}, format="json")
    assert res.status_code == 200
    assert "access" in res.data
    assert res.data["user"]["username"] == user.username


@pytest.mark.django_db
def test_login_wrong_password(client, user):
    res = client.post(LOGIN_URL, {"username": user.username, "password": "wrong"}, format="json")
    assert res.status_code == 401


@pytest.mark.django_db
def test_login_nonexistent_user(client):
    res = client.post(LOGIN_URL, {"username": "nobody", "password": "pw"}, format="json")
    assert res.status_code == 401


# ── Me API ──────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_me_unauthenticated(client):
    res = client.get(ME_URL)
    assert res.status_code == 401


@pytest.mark.django_db
def test_me_returns_user_info(auth_client):
    client, user, _ = auth_client
    res = client.get(ME_URL)
    assert res.status_code == 200
    assert res.data["user"]["username"] == user.username


# ── 로그아웃 API ────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_logout_success(auth_client):
    client, _, refresh_token = auth_client
    res = client.post(LOGOUT_URL, {"refresh": refresh_token}, format="json")
    assert res.status_code == 200


@pytest.mark.django_db
def test_logout_without_refresh_token(auth_client):
    client, _, _ = auth_client
    res = client.post(LOGOUT_URL, {}, format="json")
    assert res.status_code == 400
