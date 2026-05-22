import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import PatentProject, InventionInput
from django.shortcuts import get_object_or_404
from .models import PatentProject, InventionInput, ConsultationState, ChatMessage, DetailElement
from django.http import JsonResponse
from .ai_agent import DjangoPatentConsultant
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.files.storage import FileSystemStorage
from .utils import extract_text_from_pdf, extract_text_from_docx, extract_text_from_hwp
import os
import logging
from agents.core.graph import build_patent_graph

logger = logging.getLogger(__name__)

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
    invention_input = get_object_or_404(InventionInput, project=project)
    consultation_state, _ = ConsultationState.objects.get_or_create(project=project)
    
    #if not project.chat_messages.exists():
    #    agent = DjangoPatentConsultant(project)
    #    agent.generate_welcome_message()

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

@login_required(login_url='/accounts/login/')
@require_POST
def welcome_api(request, project_id):
    project = get_object_or_404(PatentProject, id=project_id, owner=request.user)

    if project.chat_messages.filter(role='assistant').exists():
            state = ConsultationState.objects.get(project=project)
            return JsonResponse({
                'status': 'already_exists',
                'extracted_data': {
                    'problem': state.ext_problem or '미파악',
                    'solution': state.ext_solution or '미파악',
                    'differentiation': state.ext_differentiation or '미파악',
                    'effect': state.ext_effect or '미파악'
                }
            })
    agent = DjangoPatentConsultant(project)
    ai_response = agent.generate_welcome_message()
    state = ConsultationState.objects.get(project=project)

    return JsonResponse({
        'status': 'success',
        'ai_message': ai_response,
        'extracted_data': {
            'problem': state.ext_problem or '미파악',
            'solution': state.ext_solution or '미파악',
            'differentiation': state.ext_differentiation or '미파악',
            'effect': state.ext_effect or '미파악'
        }
    })

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

@login_required(login_url='/accounts/login/')
@require_POST 
def delete_project(request, project_id):
    project = get_object_or_404(PatentProject, id=project_id, owner=request.user)
    
    title = project.title
    project.delete()  
    
    messages.success(request, f"'{title}' 프로젝트가 삭제되었습니다.")
    return redirect('dashboard')

@login_required(login_url='/accounts/login/')
@require_POST
def upload_file_api(request, project_id):
    project = get_object_or_404(PatentProject, id=project_id, owner=request.user)

    if 'file' not in request.FILES:
        return JsonResponse({'status': 'error', 'message': '파일이 전달되지 않았습니다.'})
    
    uploaded_file = request.FILES['file']
    fs = FileSystemStorage()

    filename = fs.save(uploaded_file.name, uploaded_file)
    file_path = fs.path(filename)

    ext = os.path.splitext(filename)[1].lower()
    extracted_text = ""

    try:
        if ext == '.pdf':
            extracted_text = extract_text_from_pdf(file_path)
        elif ext == '.docx':
            extracted_text = extract_text_from_docx(file_path)
        elif ext == '.hwp':
            extracted_text = extract_text_from_hwp(file_path)
        else:
            return JsonResponse({'status': 'error', 'message': 'PDF, DOCX, HWP 파일만 지원합니다.'})
        
        if not extracted_text:
            return JsonResponse({'status': 'error', 'message': '파일에서 텍스트를 추출하지 못했습니다.'})
        
        safe_text = extracted_text[:4000] #token 제한 고려하여 최대 4000자까지만 전달
        agent = DjangoPatentConsultant(project)
        prompt_message = f"[사용자가 {uploaded_file.name} 파일을 업로드했습니다. 문서 내용은 다음과 같습니다.]\n\n{safe_text}"
        ai_response = agent.interact(prompt_message)

        state = ConsultationState.objects.get(project=project)
        extracted_data = {
            'problem': state.ext_problem or '미파악',
            'solution': state.ext_solution or '미파악',
            'differentiation': state.ext_differentiation or '미파악',
            'effect': state.ext_effect or '미파악'
        }
        

        return JsonResponse({
            'status': 'success', 
            'file_name': uploaded_file.name,
            'ai_message': ai_response,
            'extracted_data': extracted_data
        })
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@login_required(login_url='/accounts/login/')
@require_POST
def generate_claims_api(request, project_id):
    project = get_object_or_404(PatentProject, id=project_id, owner=request.user)
    state = get_object_or_404(ConsultationState, project=project)

    def is_valid(val):
        return bool(val and val.strip() != "미파악")
    
    if not all([
        is_valid(state.ext_problem), 
        is_valid(state.ext_solution), 
        is_valid(state.ext_differentiation), 
        is_valid(state.ext_effect)
    ]):
        return JsonResponse({
            'status': 'warning',
            'message': '아직 발명의 핵심 4대 요소가 모두 파악되지 않았습니다.\nAI 변리사와의 대화를 통해 좌측 패널의 빈칸을 모두 채운 후 다시 시도해 주세요!'
        })
    
    try:
        db_details = project.details.all()

        graph_elements = []
        # 최상위 메인 해결수단(독립항용) 배치
        graph_elements.append({
            "element_id": 1,
            "description": state.ext_solution or "본 발명의 핵심 제어 시스템",
            "parent_id": None
        })

        # 유저가 채팅과 파일로 추가한 심화 정보들(종속항용)을 하위 엘리먼트로 주입
        for idx, detail in enumerate(db_details, start=2):
            graph_elements.append({
                "element_id": idx,
                "description": detail.content,
                "parent_id": 1 # 1번 메인 기술 구성을 부모로 인용하도록 계층 구조 강제 맵핑
            })

        # 랭그래프 초기 데이터셋 구성
        initial_patent_state = {
            "summary_data": {
                "problems": [state.ext_problem or "기존 기술의 명세서 기재 부족 문제"],
                "elements": graph_elements,
                "effects": [state.ext_effect or "특허 권리범위 확보 효율 증대 효과"],
                "user_confirmed": True
            }
        }

        logger.info(f"[{project.title}] 랭그래프 멀티에이전트 가동...")
        graph = build_patent_graph()
        
        # 앙상블 체인이 스스로 수정을 거쳐 최종 통과한 결과물이 리턴됩니다.
        final_output = graph.invoke(initial_patent_state)
        
        # 3. 결과 파싱 및 응답 데이터 정제
        claims_data = final_output.get("claims_data", {}).get("claims", [])
        examiner_data = final_output.get("examiner_data", {})
        loop_count = examiner_data.get('revision_count', 0)

        claim_result_text = f"📜 **[AI 멀티에이전트 최종 청구범위 발행 완료]**\n(AI 심사관 검수 통과: {loop_count}회 루프)\n\n"

        for c in claims_data:
            type_badge = '[종속항]' if c.get('is_dependent') else '[독립항]'
            claim_result_text += f"**청구항 {c.get('claim_no')} {type_badge}**\n{c.get('content')}\n\n"

        ChatMessage.objects.create(
            project=project,
            role='assistant',
            content=claim_result_text
        )

        return JsonResponse({
            'status': 'success',
            'message_content': claim_result_text
        })

    except Exception as e:
        logger.error(f"랭그래프 청구항 생성 에러: {e}")
        return JsonResponse({'status': 'error', 'message': f"청구항 생성 중 AI 엔진 오류가 발생했습니다: {str(e)}"})
    
