from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """유저 정보 직렬화 (응답용)"""

    gender_display = serializers.CharField(source='get_gender_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'name', 'gender', 'gender_display',
            'age', 'is_login', 'date_joined',
        ]
        read_only_fields = ['id', 'is_login', 'date_joined']


class SignupSerializer(serializers.ModelSerializer):
    """회원가입 직렬화"""

    password  = serializers.CharField(write_only=True, min_length=8, label='비밀번호')
    password2 = serializers.CharField(write_only=True, label='비밀번호 확인')

    class Meta:
        model = User
        fields = ['username', 'name', 'gender', 'age', 'password', 'password2']

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('이미 사용 중인 아이디입니다.')
        if not value.replace('_', '').isalnum():
            raise serializers.ValidationError('아이디는 영문, 숫자, 밑줄(_)만 사용 가능합니다.')
        return value

    def validate_gender(self, value):
        if value not in ('M', 'F'):
            raise serializers.ValidationError("성별은 'M' 또는 'F' 이어야 합니다.")
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password2': '비밀번호가 일치하지 않습니다.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  # 비밀번호 해싱
        user.save()
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """프로필 수정 직렬화 (PATCH /api/auth/me/)"""

    class Meta:
        model = User
        fields = ['name', 'email']
        extra_kwargs = {
            'name':  {'required': False},
            'email': {'required': False},
        }


class LoginSerializer(serializers.Serializer):
    """로그인 직렬화"""

    username = serializers.CharField(label='아이디')
    password = serializers.CharField(write_only=True, label='비밀번호')
