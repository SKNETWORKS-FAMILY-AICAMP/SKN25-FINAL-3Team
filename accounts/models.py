from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    # 기본 유저 모델과 1:1 연결
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    role = models.CharField(max_length=20, default='inventor')