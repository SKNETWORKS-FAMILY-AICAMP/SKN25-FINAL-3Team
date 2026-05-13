from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    """커스텀 유저 매니저 - username(아이디)을 기반으로 인증"""

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('아이디(ID)는 필수입니다.')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('name', '관리자')
        extra_fields.setdefault('gender', 'M')
        extra_fields.setdefault('age', 0)
        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    커스텀 유저 모델

    DB 컬럼:
      id         - 고유번호 (자동 생성 PK)
      username   - 로그인 아이디 (unique)
      name       - 이름
      gender     - 성별 (M/F)
      age        - 나이
      password   - 비밀번호 (해시 저장)
      is_login   - 로그인 상태 (1=로그인, 0=로그아웃)
      is_active  - 계정 활성화 여부
      is_staff   - 어드민 접근 여부
      date_joined - 가입일
    """

    GENDER_CHOICES = [
        ('M', '남성'),
        ('F', '여성'),
    ]

    # ── 로그인 식별자 ──
    username = models.CharField(
        max_length=30,
        unique=True,
        verbose_name='아이디',
        help_text='영문/숫자 30자 이내',
    )

    # ── 개인 정보 ──
    name = models.CharField(max_length=50, verbose_name='이름')
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        verbose_name='성별',
    )
    age = models.PositiveSmallIntegerField(verbose_name='나이')

    # ── 상태 플래그 ──
    is_login = models.BooleanField(
        default=False,
        verbose_name='로그인 상태',
        help_text='로그인=1, 로그아웃=0',
    )
    is_active = models.BooleanField(default=True, verbose_name='활성 계정')
    is_staff = models.BooleanField(default=False, verbose_name='스태프')

    # ── 날짜 ──
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name='가입일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = '사용자'
        verbose_name_plural = '사용자 목록'
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.name} ({self.username})'

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name
