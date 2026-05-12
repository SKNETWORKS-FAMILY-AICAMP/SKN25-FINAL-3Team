from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import PatentProject, InventionInput
from django.shortcuts import get_object_or_404
from .models import PatentProject, InventionInput, ConsultationState, ChatMessage
from django.http import JsonResponse
from .ai_agent import DjangoPatentConsultant
import json

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
    
    # 3. 상담 상태 및 채팅 내역 (우측 패널용)
    consultation_state, created = ConsultationState.objects.get_or_create(project=project)
    chat_messages = project.chat_messages.all().order_by('created_at')
    
    context = {
        'project': project,
        'invention_input': invention_input,
        'consultation_state': consultation_state,
        'chat_messages': chat_messages,
    }
    
    return render(request, 'workspace/workstation.html', context)

@login_required
def chat_api(request, project_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_input = data.get('message')
        
        project = get_object_or_404(PatentProject, id=project_id, owner=request.user)
        
        # 리팩토링한 AI 에이전트 호출
        agent = DjangoPatentConsultant(project)
        ai_response = agent.interact(user_input)
        
        return JsonResponse({
            'status': 'success',
            'ai_message': ai_response
        })
    return JsonResponse({'status': 'error'}, status=400)