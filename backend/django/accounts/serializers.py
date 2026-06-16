# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile

class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='first_name', required=False)
    gender = serializers.CharField(source='profile.gender', required=False)
    age = serializers.IntegerField(source='profile.age', required=False)
    is_login = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'email', 'gender', 'age', 'is_login']

    def get_is_login(self, obj):
        return True  # 이 API를 통해 정보가 반환된다면 로그인된 상태임