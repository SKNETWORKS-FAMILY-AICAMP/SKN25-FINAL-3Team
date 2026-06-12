from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, SignupForm


def login_view(request):
    """로그인 뷰 - 성공 시 is_login = True 저장"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # is_login 상태를 1(True)로 업데이트
            user.is_login = True
            user.save(update_fields=['is_login'])
            messages.success(request, f'환영합니다, {user.name}님! 👋')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
    else:
        form = LoginForm(request)

    return render(request, 'accounts/login.html', {'form': form})


def signup_view(request):
    """회원가입 뷰"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # 가입 직후 로그인 상태
            user.is_login = True
            user.save(update_fields=['is_login'])
            messages.success(request, f'회원가입 완료! 환영합니다, {user.name}님 🎉')
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = SignupForm()

    return render(request, 'accounts/signup.html', {'form': form})


def logout_view(request):
    """로그아웃 뷰 - is_login = False 저장"""
    if request.method == 'POST':
        if request.user.is_authenticated:
            # is_login 상태를 0(False)로 업데이트
            request.user.is_login = False
            request.user.save(update_fields=['is_login'])
        logout(request)
        messages.info(request, '로그아웃되었습니다.')
    return redirect('accounts:login')


@login_required
def dashboard_view(request):
    """로그인 후 대시보드"""
    return render(request, 'accounts/dashboard.html', {'user': request.user})
