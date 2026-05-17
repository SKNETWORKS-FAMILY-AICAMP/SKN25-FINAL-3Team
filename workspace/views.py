import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import PatentProject, InventionInput
from django.shortcuts import get_object_or_404
from .models import PatentProject, InventionInput, ConsultationState, ChatMessage
from django.http import JsonResponse
from .ai_agent import DjangoPatentConsultant
from django.contrib import messages

@login_required(login_url='/accounts/login/')
def dashboard(request):
    try:
        user_role = request.user.userprofile.role
    except:
        user_role = 'inventor'

    if user_role == 'attorney':
        projects = PatentProject.objects.filter(status='review')
        template_name = 'workspace/attorney_dashboard.html'
    else:
        projects = PatentProject.objects.filter(owner=request.user)
        template_name = 'workspace/inventor_dashboard.html'

    return render(request, template_name, {'projects': projects})

@login_required(login_url='/accounts/login/')
def create_project(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        problem = request.POST.get('problem_to_solve')
        prior_art = request.POST.get('prior_art_problem')
        core = request.POST.get('core_tech')
        effect = request.POST.get('expected_effect')

        project = PatentProject.objects.create(title=title,owner=request.user)
        
        # 발명 내용 저장
        # (여기에 원본 데이터에 대한 SHA-256 해시를 생성하여 project.original_data_hash에 저장하는 로직 추가 가능)
        InventionInput.objects.create(
            project=project,
            problem_to_solve=problem,
            prior_art_problem=prior_art,
            core_tech=core,
            expected_effect=effect 
        )
        
        return redirect('dashboard')
        
    return render(request, 'workspace/create_project.html')

@login_required(login_url='/accounts/login/')
def workstation(request, project_id):
    project = get_object_or_404(PatentProject, id=project_id, owner=request.user)
    
    # 2. 원본 발명 데이터 (좌측 패널용)
    invention_input = get_object_or_404(InventionInput, project=project)
    # 2. 상담 상태 (추출된 4대 요소 포함)
    consultation_state, _ = ConsultationState.objects.get_or_create(project=project)
    
    # 3. ai가 추출한 알고리즘 단계 및 심화 정보 가져오기
    algorithm_steps = project.algorithm_steps.all().order_by('step_seq')
    details = project.details.all()

    chat_messages = project.chat_messages.all().order_by('created_at')
    context = {
        'project': project,
        'invention_input': invention_input,
        'consultation_state': consultation_state,
        'algorithm_steps': algorithm_steps,
        'details': details,
        'chat_messages': chat_messages,
    }
    
    return render(request, 'workspace/workstation.html', context)

@login_required
def chat_api(request, project_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_input = data.get('message')
        
        project = get_object_or_404(PatentProject, id=project_id, owner=request.user)
        agent = DjangoPatentConsultant(project)
        ai_response = agent.interact(user_input)
        state = project.consultation_state
        
        return JsonResponse({
            'status': 'success',
            'ai_message': ai_response,
            'extracted_data': {
                'problem': state.ext_problem,
                'solution': state.ext_solution,
                'differentiation': state.ext_differentiation,
                'effect': state.ext_effect,
                'phase': state.phase
            }
        })
    return JsonResponse({'status': 'error'}, status=400)

@login_required(login_url='/accounts/login/')
def my_page(request):
    user = request.user
    try:
        user_role = user.userprofile.role
    except:
        user_role = 'inventor'

    if request.method == 'POST':
        user.first_name = request.POST.get('name', user.first_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        messages.success(request, '회원 정보가 성공적으로 변경되었습니다.')
        return redirect('my_page')
    
    user_projects = PatentProject.objects.filter(owner=user)
    
    project_stats = {
        'draft': user_projects.filter(status='draft').count(),
        'agent_processing': user_projects.filter(status='agent_processing').count(),
        'review': user_projects.filter(status='review').count(),
        'done': user_projects.filter(status='done').count(),
        'total': user_projects.count()
    }

    context = {
        'user': user,
        'user_role': user_role,
        'role_display': '전문 변리사 (Attorney)' if user_role == 'attorney' else '발명가 (Inventor)',
        'project_stats': project_stats, # 템플릿으로 통계 데이터 전달
    }
    
    return render(request, 'workspace/my_page.html', context)
