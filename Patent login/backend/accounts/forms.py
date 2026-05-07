from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class LoginForm(AuthenticationForm):
    """로그인 폼 - 아이디 + 비밀번호"""

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': '아이디를 입력하세요',
            'autocomplete': 'username',
            'id': 'id_username',
        }),
        label='아이디',
        max_length=30,
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': '비밀번호를 입력하세요',
            'autocomplete': 'current-password',
            'id': 'id_password',
        }),
        label='비밀번호',
    )

    error_messages = {
        'invalid_login': '아이디 또는 비밀번호가 올바르지 않습니다.',
        'inactive': '비활성화된 계정입니다.',
    }


class SignupForm(forms.ModelForm):
    """회원가입 폼 - 아이디/이름/성별/나이/비밀번호"""

    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'placeholder': '아이디를 입력하세요 (영문/숫자)',
            'id': 'id_signup_username',
        }),
        label='아이디',
    )
    name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': '이름을 입력하세요',
            'id': 'id_name',
        }),
        label='이름',
    )
    gender = forms.ChoiceField(
        choices=[('', '성별을 선택하세요'), ('M', '남성'), ('F', '여성')],
        widget=forms.Select(attrs={
            'id': 'id_gender',
        }),
        label='성별',
    )
    age = forms.IntegerField(
        min_value=1,
        max_value=150,
        widget=forms.NumberInput(attrs={
            'placeholder': '나이를 입력하세요',
            'id': 'id_age',
            'min': '1',
            'max': '150',
        }),
        label='나이',
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': '비밀번호를 입력하세요 (8자 이상)',
            'id': 'id_password1',
        }),
        label='비밀번호',
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': '비밀번호를 다시 입력하세요',
            'id': 'id_password2',
        }),
        label='비밀번호 확인',
    )

    class Meta:
        model = User
        fields = ['username', 'name', 'gender', 'age']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('이미 사용 중인 아이디입니다.')
        if not username.replace('_', '').isalnum():
            raise forms.ValidationError('아이디는 영문, 숫자, 밑줄(_)만 사용 가능합니다.')
        return username

    def clean_gender(self):
        gender = self.cleaned_data.get('gender')
        if not gender:
            raise forms.ValidationError('성별을 선택해주세요.')
        return gender

    def clean_password2(self):
        pw1 = self.cleaned_data.get('password1')
        pw2 = self.cleaned_data.get('password2')
        if pw1 and pw2 and pw1 != pw2:
            raise forms.ValidationError('비밀번호가 일치하지 않습니다.')
        if pw1 and len(pw1) < 8:
            raise forms.ValidationError('비밀번호는 최소 8자 이상이어야 합니다.')
        return pw2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user
