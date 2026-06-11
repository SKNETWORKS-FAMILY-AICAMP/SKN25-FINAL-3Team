from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [('inventor', '발명가'), ('attorney', '변리사')]
    name = models.CharField(max_length=100, blank=True, verbose_name='이름')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='inventor', verbose_name='가입 유형')

    class Meta:
        verbose_name = '사용자'
        verbose_name_plural = '사용자 목록'

    def __str__(self):
        return self.username
