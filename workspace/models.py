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
    
    # 원본 데이터의 해시값을 저장하는 필드 (중복 방지 및 변경 감지용)
    original_data_hash = models.CharField(max_length=64, blank=True, null=True) 
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class InventionInput(models.Model):
    project = models.OneToOneField(PatentProject, on_delete=models.CASCADE)
    problem_to_solve = models.TextField(verbose_name="해결하고자 하는 과제")
    prior_art_problem = models.TextField(verbose_name="기존 기술의 문제점")
    core_tech = models.TextField(verbose_name="핵심 기술 구성")
    expected_effect = models.TextField(verbose_name="기대 효과", blank=True, null=True)