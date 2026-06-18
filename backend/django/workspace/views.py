import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import PatentProject, InventionInput, ConsultationState, ChatMessage, PatentClaim, PatentClaim, PatentDrawingFile, PriorArtReport, SpecificationDocument
from django.http import JsonResponse, StreamingHttpResponse
from .ai_agent import DjangoPatentConsultant
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.files.storage import FileSystemStorage
from .utils import extract_text_from_pdf, extract_text_from_docx, extract_text_from_hwp
import os
import logging
#from agents.core.graph import build_patent_graph
#from agents.core.graph import app as patent_graph
#from agents.core.graph import build_patent_graph as patent_graph
#from agents.core.state import PatentState, ParsedInvention
#from agents.summary_agent import SummaryAgent 
#from agents.drawing_agent import SmartDrawingAgent 
from django.conf import settings
#from agents.specification.specification_agent import run_specification_agent
#from agents.specification.specification_storage import convert_to_markdown_format
from pydantic import BaseModel
from datetime import datetime
import httpx
from asgiref.sync import sync_to_async
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication
from asgiref.sync import async_to_sync





logger = logging.getLogger(__name__)

# 헬퍼 함수 (비동기 처리)
@sync_to_async
def get_project_data(project_id, user):
    project = get_object_or_404(PatentProject, id=project_id, owner=user)
    state = get_object_or_404(ConsultationState, project=project)
    inv_input = getattr(project, 'inventioninput', None)
    return project, state, inv_input

@sync_to_async
def save_final_data(project, data):
    # 채팅 기록 저장
    ChatMessage.objects.create(project=project, role='assistant', content=data.get("message_content", ""))
    
    # 선기조 결과 저장
    if data.get("prior_art_data"):
        pa_data = data["prior_art_data"]
        from .models import PriorArtReport # 순환참조 방지
        PriorArtReport.objects.update_or_create(
            project=project,
            defaults={
                'risk_level': pa_data.get('overall_risk', {}).get('level', 'unknown'),
                'analysis_summary': pa_data.get('analysis_summary', ''),
                'full_json_data': pa_data
            }
        )
@sync_to_async
def save_prior_art_data_only(project, data):
    """스트리밍 도중 prior_art_done 스텝이 오면 선기조 데이터만 즉시 DB에 저장합니다."""
    if data.get("prior_art_data"):
        pa_data = data["prior_art_data"]
        from .models import PriorArtReport
        PriorArtReport.objects.update_or_create(
            project=project,
            defaults={
                'risk_level': pa_data.get('overall_risk', {}).get('level', 'unknown'),
                'analysis_summary': pa_data.get('analysis_summary', ''),
                'full_json_data': pa_data
            }
        )

@sync_to_async
def save_drawings_data(project, drawings_data):
    chat_content = "[AI 특허 도면 생성 완료]\n요청하신 발명의 구성도와 흐름도입니다.\n\n"
    drawing_urls = []
    
    for dwg in drawings_data:
        web_url = f"{settings.MEDIA_URL}drawings/{dwg['file_name']}"
        drawing_urls.append({"title": dwg['title'], "url": web_url})
        chat_content += f"- **{dwg['fig_no']}**: {dwg['title']}\n"

        PatentDrawingFile.objects.create(
            project=project,
            title=dwg['title'],
            image_url=web_url
        )
    ChatMessage.objects.create(project=project, role='assistant', content=chat_content)
    return chat_content, drawing_urls

@sync_to_async
def get_spec_inputs(project):
    saved_claims = list(project.claims.all())
    saved_drawings = list(project.drawings.all())
    return saved_claims, saved_drawings

@sync_to_async
def save_spec_data(project, md_content):
    SpecificationDocument.objects.update_or_create(
        project=project, defaults={'markdown_content': md_content}
    )
    chat_message = "📝 **[AI 발명의 설명(명세서 본문) 작성 완료]**\n명세서 초안 작성이 완료되었습니다. 아래 마크다운 내용을 확인해 주세요!\n\n"
    ChatMessage.objects.create(project=project, role='assistant', content=chat_message)
    ChatMessage.objects.create(project=project, role='assistant', content=md_content)
    return chat_message

@login_required(login_url='/accounts/login/')
def dashboard(request):
    try:
        user_role = request.user.userprofile.role
    except:
        user_role = 'inventor'

    if user_role == 'attorney':
        projects = PatentProject.objects.filter(status='review')
        projects = PatentProject.objects.filter(owner=request.user)
        template_name = 'workspace/attorney_dashboard.html'
    else:
        projects = PatentProject.objects.filter(owner=request.user)
        template_name = 'workspace/inventor_dashboard.html'

    return render(request, template_name, {'projects': projects})

@api_view(['POST'])
@permission_classes([IsAuthenticated])  # JWT 토큰이 유효한 로그인 유저만 접근 가능하게 보호
def create_project(request):
    # React(Axios/Fetch)에서 보낸 JSON 데이터는 request.POST가 아니라 request.data로 받습니다.
    data = request.data
    #print("🎯 프론트엔드가 보낸 데이터:", data)
    title = data.get('title')
    problem = data.get('problem_to_solve')
    prior_art = data.get('prior_art_problem')
    core = data.get('core_tech')
    effect = data.get('expected_effect')

    # 간단한 유효성 검사 (필수 값 확인)
    if not title:
        return Response({"error": "프로젝트 제목을 입력해 주세요."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 프로젝트 생성 (request.user는 JWT 토큰을 해독하여 자동으로 매핑됨)
        project = PatentProject.objects.create(title=title, owner=request.user)
        
        # 발명 내용 저장
        # (여기에 원본 데이터에 대한 SHA-256 해시를 생성하여 project.original_data_hash에 저장하는 로직 추가 가능)
        InventionInput.objects.create(
            project=project,
            problem_to_solve=problem,
            prior_art_problem=prior_art,
            core_tech=core,
            expected_effect=effect 
        )
        
        # redirect 대신 성공했다는 메시지와 방금 만든 프로젝트 ID를 JSON으로 반환
        return Response({
            "message": "프로젝트가 성공적으로 생성되었습니다.",
            "project_id": project.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        # DB 저장 중 오류가 발생하면 500 에러와 함께 원인 반환
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def workstation(request, project_id):
    project = get_object_or_404(PatentProject, id=project_id, owner=request.user)

    if not project.chat_messages.exists():
        agent = DjangoPatentConsultant(project)
        agent.generate_welcome_message()
    
    invention_input = InventionInput.objects.filter(project=project).first()
    consultation_state = ConsultationState.objects.filter(project=project).first()
    prior_art = PriorArtReport.objects.filter(project=project).first()
    
    # 채팅 내역 가져오기 (오래된 순)
    chat_messages = project.chat_messages.all().order_by('created_at')
    
    # 3. React가 기다리는 형태(workspace.ts의 WorkstationData)에 딱 맞게 JSON을 조립합니다.
    data = {
        "project": {
            "id": project.id,
            "title": project.title,
            "created_at": project.created_at.isoformat(),
            "status": getattr(project, 'status', 'ready'),
            "has_claims": getattr(project, 'has_claims', False)
        },
        "invention_input": {
            "problem_to_solve": invention_input.problem_to_solve if invention_input else "",
            "prior_art_problem": invention_input.prior_art_problem if invention_input else "",
            "core_tech": invention_input.core_tech if invention_input else "",
            "expected_effect": invention_input.expected_effect if invention_input else "",
        },
        "consultation_state": {
            "ext_problem": consultation_state.ext_problem if consultation_state else "",
            "ext_solution": consultation_state.ext_solution if consultation_state else "",
            "ext_differentiation": consultation_state.ext_differentiation if consultation_state else "",
            "ext_effect": consultation_state.ext_effect if consultation_state else "",
        } if consultation_state else {},
        "chat_messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content
            } for msg in chat_messages
        ],
        "prior_art_data": prior_art.full_json_data if prior_art else None
    }
    
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def welcome_api(request, project_id):
    project = get_object_or_404(PatentProject, id=project_id, owner=request.user)

    # 이미 조수(assistant)의 메시지가 있다면 생성하지 않고 기존 상태만 반환
    if project.chat_messages.filter(role='assistant').exists():
        state = getattr(project, 'consultationstate', None)
        return Response({
            'status': 'already_exists',
            'extracted_data': {
                'ext_problem': state.ext_problem if state and state.ext_problem else '미파악',
                'ext_solution': state.ext_solution if state and state.ext_solution else '미파악',
                'ext_differentiation': state.ext_differentiation if state and state.ext_differentiation else '미파악',
                'ext_effect': state.ext_effect if state and state.ext_effect else '미파악'
            }
        })
        
    # 메시지가 없다면 AI 에이전트를 불러와 생성
    agent = DjangoPatentConsultant(project)
    ai_response = agent.generate_welcome_message()
    state = getattr(project, 'consultationstate', None)

    state = ConsultationState.objects.filter(project=project).first()

    return Response({
        'status': 'success',
        'ai_message': ai_response,
        'extracted_data': {
            'ext_problem': state.ext_problem if state and state.ext_problem else '미파악',
            'ext_solution': state.ext_solution if state and state.ext_solution else '미파악',
            'ext_differentiation': state.ext_differentiation if state and state.ext_differentiation else '미파악',
            'ext_effect': state.ext_effect if state and state.ext_effect else '미파악'
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_api(request, project_id):
    # 1. request.body(json.loads) 대신 DRF의 request.data를 사용합니다.
    user_input = request.data.get('message')
    
    if not user_input:
        return Response({'status': 'error', 'message': '입력된 메시지가 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
    project = get_object_or_404(PatentProject, id=project_id, owner=request.user)
    
    # 2. AI 상담원과 상호작용하여 답변을 받아옵니다.
    agent = DjangoPatentConsultant(project)
    ai_response = agent.interact(user_input)
    
    # 3. AI가 방금 업데이트한 상태를 안전하게 가져옵니다. (역참조 에러 방지)
    state = ConsultationState.objects.filter(project=project).first()
    
    # 4. 프론트엔드가 찾는 이름(ext_...)에 맞춰서 응답을 보냅니다.
    return Response({
        'status': 'success',
        'ai_message': ai_response,
        'extracted_data': {
            'ext_problem': state.ext_problem if state and state.ext_problem else '미파악',
            'ext_solution': state.ext_solution if state and state.ext_solution else '미파악',
            'ext_differentiation': state.ext_differentiation if state and state.ext_differentiation else '미파악',
            'ext_effect': state.ext_effect if state and state.ext_effect else '미파악',
            'phase': getattr(state, 'phase', 'unknown') if state else 'unknown'
        }
    })

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


@csrf_exempt
async def generate_claims_api(request, project_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    # JWT 인증 직접 처리
    from rest_framework_simplejwt.authentication import JWTAuthentication
    jwt_auth = JWTAuthentication()
    try:
        auth_result = await sync_to_async(jwt_auth.authenticate)(request)
        if auth_result is None:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        user, _ = auth_result
    except Exception:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    # DB 조회
    project = await sync_to_async(
        lambda: PatentProject.objects.filter(id=project_id, owner=user).first()
    )()
    if not project:
        return JsonResponse({'error': 'Not found'}, status=404)

    state = await sync_to_async(
        lambda: ConsultationState.objects.filter(project=project).first()
    )()
    inv_input = await sync_to_async(
        lambda: InventionInput.objects.filter(project=project).first()
    )()

    def is_valid(val):
        return bool(val and val.strip() != "미파악")

    if not state or not all([
        is_valid(state.ext_problem),
        is_valid(state.ext_solution),
        is_valid(state.ext_differentiation),
        is_valid(state.ext_effect)
    ]):
        return JsonResponse({
            'status': 'warning',
            'message': '아직 발명의 핵심 4대 요소가 모두 파악되지 않았습니다.\nAI 변리사와의 대화를 통해 좌측 패널의 빈칸을 모두 채운 후 다시 시도해 주세요!'
        })

    mock_input_data = {
        "title": project.title,
        "prior_art_problem": inv_input.prior_art_problem if inv_input else state.ext_problem,
        "problem_to_solve": inv_input.problem_to_solve if inv_input else state.ext_problem,
        "core_tech": inv_input.core_tech if inv_input else state.ext_solution,
        "expected_effect": inv_input.expected_effect if inv_input else state.ext_effect
    }

    initial_state = {
        "mock_input_data": mock_input_data,
        "summary_data": None, "claims_data": None, "examiner_data": None,
        "drawing_spec": None, "prior_art_data": None
    }

    async def event_stream():
        fastapi_url = "http://127.0.0.1:8001/api/v1/generate-claims"
        payload = {"initial_state": initial_state}
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", fastapi_url, json=payload) as r:
                    async for chunk in r.aiter_bytes():
                        if chunk:
                            try:
                                text = chunk.decode('utf-8')
                                for line in text.strip().split('\n'):
                                    if line:
                                        parsed = json.loads(line)
                                        if parsed.get("step") == "prior_art_done":
                                            await save_prior_art_data_only(project, parsed)
                                            
                                        if parsed.get("step") == "done":
                                            await save_final_data(project, parsed)
                            except Exception:
                                pass
                            yield chunk
        except httpx.RequestError as e:
            yield (json.dumps({"step": "error", "message": f"AI 서버 통신 오류: {str(e)}"}) + "\n").encode()
        
    response = StreamingHttpResponse(event_stream(), content_type='application/x-ndjson')
    response['X-Accel-Buffering'] = 'no'
    response['Cache-Control'] = 'no-cache'
    return response  

@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def save_claims_api(request, project_id):
    project = get_object_or_404(PatentProject, id=project_id, owner=request.user)
    try:
        claims_list = request.data.get('claims', [])
        if not claims_list:
            return Response({'status': 'error', 'message': '저장할 청구항 데이터가 없습니다.'})
        
        project.claims.all().delete()
        claims_to_create = [
            PatentClaim(
                project=project, claim_no=c.get('claim_no'),
                is_dependent=c.get('is_dependent', False), cited_claim_no=c.get('cited_claim_no', []),
                category=c.get('category', ''), content=c.get('content', '')
            ) for c in claims_list
        ]
        PatentClaim.objects.bulk_create(claims_to_create)
        return Response({'status': 'success'})
    except Exception as e:
        return Response({'status': 'error', 'message': str(e)})
    
@csrf_exempt
@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def manage_claims_api(request, project_id):
    project = get_object_or_404(PatentProject, id=project_id, owner=request.user)

    if request.method == 'GET':
        claims = project.claims.all()
        if not claims.exists():
            return Response({'status': 'empty', 'message': '저장된 청구항이 없습니다.'})
        
        claims_data = [{
            'id': c.id, 'claim_no': c.claim_no, 'is_dependent': c.is_dependent,
            'category': c.category, 'cited_claim_no': c.cited_claim_no, 'content': c.content
        } for c in claims]
        return Response({'status': 'success', 'claims': claims_data})

    elif request.method == 'POST':
        try:
            updated_claims = request.data.get('claims', [])
            for item in updated_claims:
                claim = PatentClaim.objects.get(id=item['id'], project=project)
                claim.content = item.get('content', claim.content)
                if 'category' in item: claim.category = item['category']
                if 'cited_claim_no' in item: claim.cited_claim_no = item['cited_claim_no']
                claim.save()
            return Response({'status': 'success'})
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)})
        
@login_required(login_url='/accounts/login/')
@require_POST
def bulk_delete_projects_api(request):
    try:
        data = json.loads(request.body)
        project_ids = data.get('project_ids', [])

        if not project_ids:
            return JsonResponse({'status': 'error', 'message': '삭제할 프로젝트가 선택되지 않았습니다.'})

        deleted_count, _ = PatentProject.objects.filter(
            id__in=project_ids, 
            owner=request.user
        ).delete()

        return JsonResponse({'status': 'success', 'deleted_count': deleted_count})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
    

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def patent_report_api(request, project_id):
    project = get_object_or_404(PatentProject, id=project_id, owner=request.user)
    
    # 🎯 404 HTML 에러 방지를 위해 get_object_or_404 대신 filter().first()를 사용합니다!
    state = ConsultationState.objects.filter(project=project).first()

    # 데이터 가져오기
    invention_input = getattr(project, 'inventioninput', None)
    claims = project.claims.all().order_by('claim_no')
    specification = getattr(project, 'specification_doc', None)
    drawings = PatentDrawingFile.objects.filter(project=project)

    # 🎯 리액트가 찰떡같이 알아먹을 수 있도록 JSON으로 포장해서 반환합니다.
    return Response({
        "status": "success",
        "project": {
            "id": project.id,
            "title": project.title,
            "created_at": project.created_at
        },
        "state": {
            "ext_problem": state.ext_problem if state else "",
            "ext_solution": state.ext_solution if state else "",
            "ext_differentiation": state.ext_differentiation if state else "",
            "ext_effect": state.ext_effect if state else "",
        },
        "claims": [
            {"id": c.id, "claim_no": c.claim_no, "content": c.content, "is_dependent": c.is_dependent} 
            for c in claims
        ],
        "drawings": [
            {"title": d.title, "image_url": d.image_url} 
            for d in drawings
        ],
        "specification": {
            "markdown_content": specification.markdown_content if specification else ""
        }
    })


@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def generate_drawings_api(request, project_id):
    # 1. 안전하고 직관적인 동기식(Sync) DB 조회
    project = get_object_or_404(PatentProject, id=project_id, owner=request.user)
    state = ConsultationState.objects.filter(project=project).first()
    inv_input = InventionInput.objects.filter(project=project).first()

    if not state:
        return Response({'status': 'error', 'message': '발명 분석 상태가 존재하지 않습니다.'})

    # 2. FastAPI로 보낼 데이터 준비
    mock_input_data = {
        "title": project.title,
        "prior_art_problem": inv_input.prior_art_problem if inv_input else state.ext_problem,
        "problem_to_solve": inv_input.problem_to_solve if inv_input else state.ext_problem,
        "core_tech": inv_input.core_tech if inv_input else state.ext_solution,
        "expected_effect": inv_input.expected_effect if inv_input else state.ext_effect
    }

    fastapi_url = "http://127.0.0.1:8001/api/v1/generate-drawings"

    try:
        # 3. 비동기 오류(Deadlock)를 원천 차단하기 위해 동기식(Sync) 클라이언트를 사용합니다.
        with httpx.Client(timeout=120.0) as client: 
            resp = client.post(fastapi_url, json={"mock_input_data": mock_input_data})
            resp.raise_for_status()
            data = resp.json()
            
        if data.get("status") == "success":
            # 4. DB 저장 로직 (에러가 나지 않도록 직관적으로 코드 내부에 병합)
            drawings_data = data["drawings"]
            chat_content = "[AI 특허 도면 생성 완료]\n요청하신 발명의 구성도와 흐름도입니다.\n\n"
            drawing_urls = []
            
            for dwg in drawings_data:
                raw_url = f"{settings.MEDIA_URL}drawings/{dwg['file_name']}"
                web_url = request.build_absolute_uri(raw_url)
                
                drawing_urls.append({"title": dwg['title'], "url": web_url})
                
                chat_content += f"**도면 {dwg['fig_no']}**: {dwg['title']}\n![{dwg['title']}]({web_url})\n\n"

                PatentDrawingFile.objects.create(
                    project=project,
                    title=dwg['title'],
                    image_url=web_url
                )
            
            # AI가 도면을 전달했다는 채팅 메시지 생성
            ChatMessage.objects.create(project=project, role='assistant', content=chat_content)

            # DRF Response로 안전하게 프론트엔드로 반환
            return Response({
                "status": "success",
                "message": chat_content,
                "drawings": drawing_urls
            })
        else:
            return Response({"status": "error", "message": data.get("message")})
            
    except Exception as e:
        logger.error(f"도면 API 에러: {e}")
        return Response({"status": "error", "message": f"도면 생성 중 서버 오류 발생: {str(e)}"})
    


def convert_to_markdown_format(invention_title: str, spec_dict: dict) -> str:
    """FastAPI에서 받아온 명세서 dict를 Markdown 문자열로 변환합니다."""
    
    spec = spec_dict.get("specification", spec_dict)
    if not isinstance(spec, dict):
        spec = spec_dict

    technical_field = str(spec.get("technical_field") or spec_dict.get("technical_field") or "").strip()
    background_art = str(spec.get("background_art") or spec_dict.get("background_art") or "").strip()
    problem_to_solve = str(spec.get("problem_to_solve") or spec_dict.get("problem_to_solve") or "").strip()
    means_for_solving = str(spec.get("means_for_solving") or spec_dict.get("means_for_solving") or "").strip()
    effects = str(spec.get("effects") or spec_dict.get("effects") or "").strip()
    brief_description_of_drawings = str(spec.get("brief_description_of_drawings") or spec_dict.get("brief_description_of_drawings") or "").strip()
    detailed_description = str(spec.get("detailed_description") or spec_dict.get("detailed_description") or "").strip()

    markdown_content = f"""# [특허 명세서] 발명의 설명

## 발명의 명칭
{invention_title}

## 기술분야
{technical_field}

## 배경기술
{background_art}

## 해결하고자 하는 과제
{problem_to_solve}

## 과제의 해결수단
{means_for_solving}

## 발명의 효과
{effects}

## 도면의 간단한 설명
{brief_description_of_drawings}

## 발명을 실시하기 위한 구체적인 내용
{detailed_description}"""

    return markdown_content


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def generate_specification_api(request, project_id):
    # 1. 기존 비동기 헬퍼 함수들을 동기식 환경에서 안전하게 호출합니다.
    try:
        project, state, _ = async_to_sync(get_project_data)(project_id, request.user)
        saved_claims, saved_drawings = async_to_sync(get_spec_inputs)(project)
    except Exception as e:
        return Response({'status': 'error', 'message': f'데이터 조회 실패: {str(e)}'}, status=404)

    # 2. FastAPI로 보낼 상태(State) 데이터 조립
    draft_claims = [
        {
            "claim_no": c.claim_no, "text": c.content,
            "type": "dependent" if c.is_dependent else "independent",
            "category": getattr(c, 'category', '장치')
        } for c in saved_claims
    ]

    figures = [
        {
            "fig_no": i + 1, "title": d.title,
            "brief_description": f"본 발명의 실시예에 따른 {d.title}이다."
        } for i, d in enumerate(saved_drawings)
    ]

    agent_state = {
        "consultation": {
            "invention_title": project.title,
            "problem": state.ext_problem, "solution": state.ext_solution,
            "differentiation": state.ext_differentiation, "effect": state.ext_effect,
        },
        "claims": {"draft_claims": draft_claims},
        "drawings": {"figures": figures, "reference_numerals": {}},
        "drafting_options": {
            "use_subheadings_in_detailed_description": True,
            "brief_drawing_description": True, "strict_grounding": False,
            "method_step_format": {"enabled": False}
        }
    }

    fastapi_url = "http://127.0.0.1:8001/api/v1/generate-specification"

    try:
        # 3. 명세서 작성은 양이 많으므로 타임아웃을 넉넉히 300초(5분) 설정하여 호출합니다.
        with httpx.Client(timeout=300.0) as client:
            resp = client.post(fastapi_url, json={"agent_state": agent_state})
            resp.raise_for_status()
            data = resp.json()

        if data.get("status") == "success":
            result = data["result"]
            
            # 장고단에서 마크다운으로 변환 후 DB 저장 (비동기 함수들을 안전하게 래핑)
            md_content = convert_to_markdown_format(project.title, result)
            chat_message = async_to_sync(save_spec_data)(project, md_content)
            
            # 4. 깔끔하게 일반 JSON Response로 결과를 반환합니다.
            return Response({
                "status": "success",
                "message": chat_message,
                "markdown": md_content,
                "details": result.get("details", {})
            })
        else:
            return Response({"status": "error", "message": data.get("message")})

    except Exception as e:
        logger.error(f"명세서 API 에러: {e}")
        return Response({"status": "error", "message": f"명세서 생성 중 서버 오류: {str(e)}"})