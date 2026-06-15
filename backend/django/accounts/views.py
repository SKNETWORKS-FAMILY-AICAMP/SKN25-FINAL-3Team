from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from accounts.models import UserProfile
from django.contrib import messages

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        user_role = request.POST.get('role', 'inventor')
        
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, role=user_role)
            messages.success(request, '회원가입이 완료되었습니다!')

            return redirect('/accounts/login/')
        else:
            messages.error(request, '회원가입에 실패했습니다. 입력 내용을 확인해주세요.')
    else:
        form = UserCreationForm()

    return render(request, 'signup.html', {'form': form})