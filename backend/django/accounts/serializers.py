# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User


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


class SignupSerializer(serializers.Serializer):
    """회원가입 API 입력 직렬화"""

    username = serializers.CharField(label='아이디')
    password = serializers.CharField(write_only=True, min_length=8, label='비밀번호')
    password2 = serializers.CharField(write_only=True, label='비밀번호 확인')
    name = serializers.CharField(required=False, allow_blank=True, label='이름')
    gender = serializers.ChoiceField(choices=(('M', 'Male'), ('F', 'Female')), required=False)
    age = serializers.IntegerField(required=False, min_value=0)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('이미 사용 중인 아이디입니다.')
        if not value.replace('_', '').isalnum():
            raise serializers.ValidationError('아이디는 영문, 숫자, 밑줄(_)만 사용 가능합니다.')
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password2': '비밀번호가 일치하지 않습니다.'})
        return data


class LoginSerializer(serializers.Serializer):
    """로그인 직렬화"""

    username = serializers.CharField(label='아이디')
    password = serializers.CharField(write_only=True, label='비밀번호')
