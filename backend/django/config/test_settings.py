import os

# load_dotenv()이 빈 값으로 덮어쓰기 전에 미리 설정합니다.
os.environ.setdefault("SECRET_KEY", "django-insecure-test-only-key-for-pytest-12345")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from config.settings import *  # noqa: F401, F403

SECRET_KEY = "django-insecure-test-only-key-for-pytest-12345"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
