from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import PatentProject, InventionInput

@login_required(login_url='/accounts/login/')
def dashboard(request):
    try:
        user_role = request.user.userprofile.role
    except:
        # 프로필이 없는 경우 기본값으로 설정
        user_role = 'inventor'

    # 2. 역할에 따라 다른 템플릿 파일 경로를 지정합니다.
    if user_role == 'attorney':
        # 변리사용 템플릿 (나중에 만드시면 됩니다)
        template_name = 'workspace/attorney_dashboard.html'
    else:
        # 발명가용 템플릿
        template_name = 'workspace/inventor_dashboard.html'

    # 3. 해당 템플릿을 화면에 그립니다.
    return render(request, template_name)

@login_required(login_url='/accounts/login/')
def create_project(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        problem = request.POST.get('problem_to_solve')
        prior_art = request.POST.get('prior_art_problem')
        core = request.POST.get('core_tech')

        project = PatentProject.objects.create(title=title,owner=request.user)
        
        # 발명 내용 저장
        # (여기에 원본 데이터에 대한 SHA-256 해시를 생성하여 project.original_data_hash에 저장하는 로직 추가 가능)
        InventionInput.objects.create(
            project=project,
            problem_to_solve=problem,
            prior_art_problem=prior_art,
            core_tech=core
        )
        
        return redirect('dashboard')
        
    return render(request, 'workspace/create_project.html')