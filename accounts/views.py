from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from accounts.models import UserProfile

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        user_role = request.POST.get('role', 'inventor')
        
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, role=user_role)
            return redirect('/accounts/login/')

    else:
        form = UserCreationForm()

    return render(request, 'signup.html', {'form': form})