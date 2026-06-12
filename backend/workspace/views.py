import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import PatentProject, InventionInput, ConsultationState, ChatMessage, PatentClaim, PatentClaim, PatentDrawingFile, PriorArtReport, SpecificationDocument
from django.http import JsonResponse
from .ai_agent import DjangoPatentConsultant
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.files.storage import FileSystemStorage
from .utils import extract_text_from_pdf, extract_text_from_docx, extract_text_from_hwp
import os
import logging
from agents.core.graph import build_patent_graph
#from agents.core.graph import app as patent_graph
from agents.core.graph import build_patent_graph as patent_graph
from agents.core.state import PatentState, ParsedInvention
from django.http import StreamingHttpResponse
from agents.summary_agent import SummaryAgent 
from agents.drawing_agent import SmartDrawingAgent 
from django.conf import settings
from agents.specification.specification_agent import run_specification_agent
from agents.specification.specification_storage import convert_to_markdown_format
from pydantic import BaseModel
from datetime import datetime

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

    prior_art_report = getattr(project, 'prior_art_report', None)
    pa_json_string = json.dumps(prior_art_report.full_json_data) if prior_art_report else "null"

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
        'prior_art_json': pa_json_string
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
    inv_input = getattr(project, 'inventioninput', None)# 기존 원본 입력 데이터 가져오기 (없을 경우를 대비한 안전망)

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
    
    
    mock_input_data = {
        "title": project.title,
        "prior_art_problem": inv_input.prior_art_problem if inv_input else state.ext_problem,
        "problem_to_solve": inv_input.problem_to_solve if inv_input else state.ext_problem,
        "core_tech": inv_input.core_tech if inv_input else state.ext_solution,
        "expected_effect": inv_input.expected_effect if inv_input else state.ext_effect
    }

    initial_state = {
        "mock_input_data": mock_input_data,
        "summary_data": None,
        "claims_data": None,
        "examiner_data": None,
        "drawing_spec": None,
        "prior_art_data": None
    }

    def event_stream():
        try:
            # 첫 번째 신호 발송
            yield json.dumps({"step": "start", "message": "에이전트 가동을 시작합니다."}) + "\n"

            compiled_graph = patent_graph() 
            #final_state = compiled_graph.invoke(initial_state)
            final_state = {}

            for output in compiled_graph.stream(initial_state):
                for node_name, state_update in output.items():
                    final_state.update(state_update)

                    safe_state = {k: safe_serialize(v) for k, v in state_update.items()}
                    yield json.dumps({
                        "step": "log_and_state",
                        "log_msg": f"[{node_name.upper()}] 에이전트 노드 처리 완료 및 State 업데이트",
                        "state_data": safe_state
                    }) + "\n"

                    if node_name == "summary_node":
                        yield json.dumps({"step": "summary", "message": "발명 내용 구조화 완료!"}) + "\n"
                    elif node_name == "claim_node":
                        yield json.dumps({"step": "claim", "message": "청구항 초안 작성 완료!"}) + "\n"
                    elif node_name == "examiner_node":
                        examiner_data = state_update.get("examiner_data")
                        if not examiner_data:
                            pass
                        if examiner_data and not examiner_data.is_approved:
                            yield json.dumps({"step": "rewrite", "message": f"심사관 반려! ({examiner_data.revision_count}차 보정 진행)"}) + "\n"
                        else:
                            yield json.dumps({"step": "examiner", "message": "심사관 승인 완료!"}) + "\n"
                    elif node_name == "rewrite_node":
                        yield json.dumps({"step": "rewrite_done", "message": "보정 완료! 재심사 요청 중..."}) + "\n"
                    

            claims_result = final_state.get("claims_data")
            examiner_result = final_state.get("examiner_data")

            if not claims_result or not claims_result.claims:
                yield json.dumps({"step": "error", "message": "AI 엔진이 청구항을 생성하지 못했습니다."}) + "\n"
                return
        
            loop_count = examiner_result.revision_count if examiner_result else 0
            claim_result_text = f"📜 **[AI 멀티에이전트 최종 청구범위 발행 완료]**\n(AI 심사관 검수 통과: {loop_count}회 루프)\n\n"

            claims_list_for_frontend = []
            for c in claims_result.claims: 
                type_badge = '[종속항]' if c.is_dependent else '[독립항]'
                claim_result_text += f"**청구항 {c.claim_no} {type_badge}**\n{c.content}\n\n"
                
                claims_list_for_frontend.append({
                    "claim_no": c.claim_no,
                    "is_dependent": c.is_dependent,
                    "cited_claim_no": c.cited_claim_no,
                    "category": c.category,
                    "content": c.content
                })

            ChatMessage.objects.create(project=project, role='assistant', content=claim_result_text)

            yield json.dumps({"step": "prior_art_start", "message": "AWS RDS 벡터DB 연결 및 선행기술조사 가동..."}) + "\n"

            try:
                from agents.prior_art_agent.prior_art_agent import run_prior_art_agent
                
                prior_art_result = run_prior_art_agent(final_state, top_n=3)
                pa_data = prior_art_result["prior_art_data"].model_dump()

                PriorArtReport.objects.update_or_create(
                    project=project,
                    defaults={
                        'risk_level': pa_data.get('overall_risk', {}).get('level', 'unknown'),
                        'analysis_summary': pa_data.get('analysis_summary', ''),
                        'full_json_data': pa_data
                    }
                )
                
                
                yield json.dumps({
                    "step": "prior_art_done", 
                    "message": "선행기술조사 완료! 리포트를 생성했습니다.",
                    "prior_art_data": pa_data
                }) + "\n"
                
            except Exception as e:
                logger.error(f"선기조 에러: {e}")
                yield json.dumps({"step": "error", "message": f"선기조 중 오류 발생: {str(e)}"}) + "\n"

            yield json.dumps({
                "step": "done",
                "message_content": claim_result_text,
                "claims": claims_list_for_frontend,
                "prior_art_data": pa_data
            }) + "\n"

        except Exception as e:
            logger.error(f"랭그래프 청구항 생성 에러: {e}")
            yield json.dumps({"step": "error", "message": f"청구항 생성 중 오류가 발생했습니다: {str(e)}"}) + "\n"

    return StreamingHttpResponse(event_stream(), content_type='application/x-ndjson')

@login_required(login_url='/accounts/login/')
@require_POST
def save_claims_api(request, project_id):
    project = get_object_or_404(PatentProject, id=project_id, owner=request.user)

    try:
        data = json.loads(request.body)
        claims_list = data.get('claims', [])

        if not claims_list:
            return JsonResponse({'status': 'error', 'message': '저장할 청구항 데이터가 없습니다.'})
        
        project.claims.all().delete()

        claims_to_create = []
        for c in claims_list:
            claims_to_create.append(
                PatentClaim(
                    project=project,
                    claim_no=c.get('claim_no'),
                    is_dependent=c.get('is_dependent', False),
                    cited_claim_no=c.get('cited_claim_no', []),
                    category=c.get('category', ''),
                    content=c.get('content', '')
                )
            )

        PatentClaim.objects.bulk_create(claims_to_create)

        return JsonResponse({'status': 'success'})
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
    
@login_required(login_url='/accounts/login/')
def manage_claims_api(request, project_id):
    project = get_object_or_404(PatentProject, id=project_id, owner=request.user)

    if request.method == 'GET':
        claims = project.claims.all() # 아까 Meta에 ordering을 해둬서 번호순으로 나옴
        if not claims.exists():
            return JsonResponse({'status': 'empty', 'message': '저장된 청구항이 없습니다. 먼저 우측 상단의 "AI 청구항 작성 시작"을 통해 초안을 생성하고 저장해 주세요.'})
            
        claims_data = [{
            'id': c.id,
            'claim_no': c.claim_no,
            'is_dependent': c.is_dependent,
            'category': c.category,
            'cited_claim_no': c.cited_claim_no,
            'content': c.content
        } for c in claims]
        
        return JsonResponse({'status': 'success', 'claims': claims_data})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            updated_claims = data.get('claims', [])

            for item in updated_claims:
                claim = PatentClaim.objects.get(id=item['id'], project=project)
                
                claim.content = item.get('content', claim.content)
                
                if 'category' in item:
                    claim.category = item['category']
                if 'cited_claim_no' in item:
                    claim.cited_claim_no = item['cited_claim_no']
                    
                claim.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
        
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
    
@login_required(login_url='/accounts/login/')
def patent_report_view(request, project_id):
    project = get_object_or_404(PatentProject, id=project_id, owner=request.user)
    state = get_object_or_404(ConsultationState, project=project)

    invention_input = getattr(project, 'inventioninput', None)
    claims = project.claims.all().order_by('claim_no')
    consultation_state = getattr(project, 'consultationstate', None)
    specification = getattr(project, 'specification_doc', None)
    drawings = PatentDrawingFile.objects.filter(project=project)

    context = {
        'project': project,
        'state': state,
        'invention_input': invention_input,
        'consultation_state': consultation_state,
        'claims': claims,
        'specification': specification,
        'drawings': drawings
    }
    return render(request, 'workspace/report.html', context)

@login_required
@require_POST
def generate_drawings_api(request, project_id):
    project = get_object_or_404(PatentProject, id=project_id, owner=request.user)
    state = get_object_or_404(ConsultationState, project=project)
    inv_input = getattr(project, 'inventioninput', None)

    try:
        mock_input_data = {
            "title": project.title,
            "prior_art_problem": inv_input.prior_art_problem if inv_input else state.ext_problem,
            "problem_to_solve": inv_input.problem_to_solve if inv_input else state.ext_problem,
            "core_tech": inv_input.core_tech if inv_input else state.ext_solution,
            "expected_effect": inv_input.expected_effect if inv_input else state.ext_effect
        }

        # 2. 요약 에이전트를 한 번 돌려서 Pydantic 객체(ParsedInvention) 추출
        # (청구항 짤 때와 동일한 데이터 구조 획득)
        summary_agent = SummaryAgent(model_name="gpt-4o-mini")
        summary_state = summary_agent.run({"mock_input_data": mock_input_data})
        
        # 3. 도면 에이전트 가동! (1초 컷)
        drawing_agent = SmartDrawingAgent()
        drawing_result = drawing_agent.run(summary_state)
        
        drawing_spec = drawing_result.get("drawing_spec")
        if not drawing_spec:
            raise Exception("도면 생성에 실패했습니다.")

        drawing_urls = []
        chat_content = "[AI 특허 도면 생성 완료]\n요청하신 발명의 구성도와 흐름도입니다.\n\n"
        
        for dwg in drawing_spec.drawings:
            file_name = os.path.basename(dwg.image_path)
            web_url = f"{settings.MEDIA_URL}drawings/{file_name}"
            drawing_urls.append({"title": dwg.title, "url": web_url})
            chat_content += f"- **{dwg.fig_no}**: {dwg.title}\n"

            PatentDrawingFile.objects.create(
                project=project,
                title=dwg.title,
                image_url=web_url
            )

        # 5. 채팅 기록 저장
        ChatMessage.objects.create(project=project, role='assistant', content=chat_content)

        return JsonResponse({
            "status": "success",
            "message": chat_content,
            "drawings": drawing_urls
        })

    except Exception as e:
        logger.error(f"도면 생성 에러: {e}")
        return JsonResponse({"status": "error", "message": str(e)})

@login_required
@require_POST
def generate_specification_api(request, project_id):
    project = get_object_or_404(PatentProject, id=project_id, owner=request.user)
    state = get_object_or_404(ConsultationState, project=project)

    try:
        saved_claims = project.claims.all() if hasattr(project, 'claims') else []
        saved_drawings = project.drawings.all() if hasattr(project, 'drawings') else []

        draft_claims = []
        for c in saved_claims:
            draft_claims.append({
                "claim_no": c.claim_no,
                "text": c.content,
                "type": "dependent" if c.is_dependent else "independent",
                "category": getattr(c, 'category', '장치')
            })

        figures = []
        for i, d in enumerate(saved_drawings):
            figures.append({
                "fig_no": i + 1,
                "title": d.title,
                "brief_description": f"본 발명의 실시예에 따른 {d.title}이다."
            })

        agent_state = {
            "consultation": {
                "invention_title": project.title,
                "problem": state.ext_problem,
                "solution": state.ext_solution,
                "differentiation": state.ext_differentiation,
                "effect": state.ext_effect,
            },
            "claims": {
                "draft_claims": draft_claims
            },
            "drawings": {
                "figures": figures,
                "reference_numerals": {} # 도면 에이전트에서 파싱한 데이터가 있다면 매핑
            },
            "drafting_options": {
                "use_subheadings_in_detailed_description": True,
                "brief_drawing_description": True,
                "strict_grounding": False,
                "method_step_format": {"enabled": False}
            }
        }

        result = run_specification_agent(agent_state)

        if result.get("status") != "ok":
            raise Exception(f"명세서 생성 실패: {result.get('warnings', ['알 수 없는 오류'])}")

        md_content = convert_to_markdown_format(project.title, result)

        SpecificationDocument.objects.update_or_create(
            project=project,
            defaults={
                'markdown_content': md_content
            }
        )

        chat_message = "📝 **[AI 발명의 설명(명세서 본문) 작성 완료]**\n명세서 초안 작성이 완료되었습니다. 아래 마크다운 내용을 확인해 주세요!\n\n"
        ChatMessage.objects.create(project=project, role='assistant', content=chat_message)
        
        ChatMessage.objects.create(project=project, role='assistant', content=md_content)

        return JsonResponse({
            "status": "success",
            "message": chat_message,
            "markdown": md_content,
            "details": result.get("details", {})
        })

    except Exception as e:
        logger.error(f"명세서 생성 에러: {e}")
        return JsonResponse({"status": "error", "message": str(e)})
    
def safe_serialize(obj):
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    return str(obj)


