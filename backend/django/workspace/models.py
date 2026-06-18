from django.db import models
from django.contrib.auth.models import User

class PatentProject(models.Model):
    STATUS_CHOICES = (
        ('draft', '초안 작성중'),
        ('agent_processing', 'AI 처리중'),
        ('review', '변리사 검토중'),
        ('done', '완료'),
    )
    title = models.CharField(max_length=200, verbose_name="프로젝트명")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    original_data_hash = models.CharField(max_length=64, blank=True, null=True) # 원본 데이터의 해시값을 저장하는 필드 (중복 방지 및 변경 감지용)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class InventionInput(models.Model):
    project = models.OneToOneField(PatentProject, on_delete=models.CASCADE)
    problem_to_solve = models.TextField(verbose_name="해결하고자 하는 과제")
    prior_art_problem = models.TextField(verbose_name="기존 기술의 문제점")
    core_tech = models.TextField(verbose_name="핵심 기술 구성")
    expected_effect = models.TextField(verbose_name="기대 효과", blank=True, null=True)

class ConsultationState(models.Model):
    project = models.OneToOneField(PatentProject, on_delete=models.CASCADE, related_name='consultation_state')
    phase = models.IntegerField(default=1)
    collecting_steps = models.BooleanField(default=False)
    ext_problem = models.TextField(blank=True, null=True)
    ext_solution = models.TextField(blank=True, null=True)
    ext_differentiation = models.TextField(blank=True, null=True)
    ext_effect = models.TextField(blank=True, null=True)

class ChatMessage(models.Model):
    project = models.ForeignKey(PatentProject, on_delete=models.CASCADE, related_name='chat_messages')
    role = models.CharField(max_length=20) # 'user', 'assistant'
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class AlgorithmStep(models.Model):
    project = models.ForeignKey(PatentProject, on_delete=models.CASCADE, related_name='algorithm_steps')
    step_seq = models.IntegerField()
    content = models.TextField()

class DetailElement(models.Model):
    project = models.ForeignKey(PatentProject, on_delete=models.CASCADE, related_name='details')
    element_type = models.CharField(max_length=50)
    content = models.TextField()

class PatentClaim(models.Model):
    project = models.ForeignKey(PatentProject, on_delete=models.CASCADE, related_name='claims')
    claim_no = models.IntegerField(verbose_name="청구항 번호")
    is_dependent = models.BooleanField(default=False, verbose_name="종속항 여부")
    cited_claim_no = models.JSONField(default=list, blank=True, verbose_name="인용항 번호 목록")
    category = models.CharField(max_length=50, verbose_name="카테고리(방법/시스템 등)")
    content = models.TextField(verbose_name="청구항 내용")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['claim_no'] 

    def __str__(self):
        return f"[{self.project.title}] 청구항 {self.claim_no}"
    
class PatentDrawingFile(models.Model):
    project = models.ForeignKey(PatentProject, on_delete=models.CASCADE, related_name='drawings')
    title = models.CharField(max_length=200)  
    image_url = models.URLField(max_length=500, help_text="S3에 업로드된 도면 이미지 URL")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.title} - {self.title}"

class PriorArtReport(models.Model):
    project = models.OneToOneField('PatentProject', on_delete=models.CASCADE, related_name='prior_art_report')
    risk_level = models.CharField(max_length=50)  # low, medium, high
    analysis_summary = models.TextField()
    full_json_data = models.JSONField()          
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.title} - 선기조 리포트"

class SpecificationDocument(models.Model):
    project = models.OneToOneField('PatentProject', on_delete=models.CASCADE, related_name='specification_doc')
    markdown_content = models.TextField()        
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.title} - 명세서 본문"