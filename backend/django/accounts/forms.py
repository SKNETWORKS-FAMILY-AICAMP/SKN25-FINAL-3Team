from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class SignupForm(UserCreationForm):
    name = forms.CharField(
        max_length=100, label='이름', required=True,
        widget=forms.TextInput(attrs={'placeholder': '이름을 입력하세요'}),
    )

    class Meta:
        model = User
        fields = ('username', 'name', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.name = self.cleaned_data['name']
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    pass
