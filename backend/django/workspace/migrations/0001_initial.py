import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PatentProject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='프로젝트명')),
                ('status', models.CharField(choices=[('draft', '초안 작성중'), ('agent_processing', 'AI 처리중'), ('review', '변리사 검토중'), ('done', '완료')], default='draft', max_length=20)),
                ('original_data_hash', models.CharField(blank=True, max_length=64, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projects', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='InventionInput',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('problem_to_solve', models.TextField(verbose_name='해결하고자 하는 과제')),
                ('prior_art_problem', models.TextField(verbose_name='기존 기술의 문제점')),
                ('core_tech', models.TextField(verbose_name='핵심 기술 구성')),
                ('expected_effect', models.TextField(blank=True, null=True, verbose_name='기대 효과')),
                ('project', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='workspace.patentproject')),
            ],
        ),
        migrations.CreateModel(
            name='ConsultationState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phase', models.IntegerField(default=1)),
                ('collecting_steps', models.BooleanField(default=False)),
                ('ext_problem', models.TextField(blank=True, null=True)),
                ('ext_solution', models.TextField(blank=True, null=True)),
                ('ext_differentiation', models.TextField(blank=True, null=True)),
                ('ext_effect', models.TextField(blank=True, null=True)),
                ('project', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='consultation_state', to='workspace.patentproject')),
            ],
        ),
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(max_length=20)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_messages', to='workspace.patentproject')),
            ],
        ),
        migrations.CreateModel(
            name='AlgorithmStep',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('step_seq', models.IntegerField()),
                ('content', models.TextField()),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='algorithm_steps', to='workspace.patentproject')),
            ],
        ),
        migrations.CreateModel(
            name='DetailElement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('element_type', models.CharField(max_length=50)),
                ('content', models.TextField()),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='details', to='workspace.patentproject')),
            ],
        ),
        migrations.CreateModel(
            name='PatentClaim',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('claim_no', models.IntegerField(verbose_name='청구항 번호')),
                ('is_dependent', models.BooleanField(default=False, verbose_name='종속항 여부')),
                ('cited_claim_no', models.JSONField(blank=True, default=list, verbose_name='인용항 번호 목록')),
                ('category', models.CharField(max_length=50, verbose_name='카테고리(방법/시스템 등)')),
                ('content', models.TextField(verbose_name='청구항 내용')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='claims', to='workspace.patentproject')),
            ],
            options={'ordering': ['claim_no']},
        ),
        migrations.CreateModel(
            name='PatentDrawingFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('image_url', models.CharField(max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='drawings', to='workspace.patentproject')),
            ],
        ),
        migrations.CreateModel(
            name='PriorArtReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('risk_level', models.CharField(max_length=50)),
                ('analysis_summary', models.TextField()),
                ('full_json_data', models.JSONField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='prior_art_report', to='workspace.patentproject')),
            ],
        ),
        migrations.CreateModel(
            name='SpecificationDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('markdown_content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='specification_doc', to='workspace.patentproject')),
            ],
        ),
    ]
