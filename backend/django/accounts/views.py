# accounts/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import render
from django.contrib.auth.models import User
from .models import UserProfile
from .serializers import UserSerializer

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# 1. 로그인 커스텀 (토큰뿐만 아니라 프론트가 원하는 user 정보와 message를 같이 반환)
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # 프론트엔드의 AuthTokens 인터페이스에 맞춤
        data['user'] = UserSerializer(self.user).data
        data['message'] = '로그인 성공'
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# 2. 회원가입 API
@api_view(['POST'])
@permission_classes([AllowAny])
def signup_api(request):
    data = request.data
    username = data.get('username')
    password = data.get('password')
    name = data.get('name', '')
    age = data.get('age')
    gender = data.get('gender')
    
    if User.objects.filter(username=username).exists():
        # 프론트엔드의 `err.error` 캐치 로직에 맞춰 반환
        return Response({'error': '이미 존재하는 아이디입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
    # 유저 생성
    user = User.objects.create_user(username=username, password=password, first_name=name)
    UserProfile.objects.create(user=user, age=age, gender=gender, role='inventor')
    
    # 가입 즉시 로그인을 위한 토큰 발급
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': UserSerializer(user).data,
        'message': '회원가입 성공'
    }, status=status.HTTP_201_CREATED)

# 3. 로그아웃 API (Refresh Token 블랙리스트 처리)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': '로그아웃 성공'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': '잘못된 토큰입니다.'}, status=status.HTTP_400_BAD_REQUEST)

# 4. 내 정보 조회 및 수정 API (/me/)
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def me_api(request):
    user = request.user
    if request.method == 'PATCH':
        data = request.data
        if 'name' in data:
            user.first_name = data['name']
        if 'email' in data:
            user.email = data['email']
        user.save()
        
    return Response({'user': UserSerializer(user).data})


def about(request):
    return render(request, 'pages/about.html')


def features(request):
    return render(request, 'pages/features.html')


def team(request):
    return render(request, 'pages/team.html')


def agents_overview(request):
    return render(request, 'pages/agents_overview.html')


AGENTS = {
    'consulting': {
        'num': 'I',
        'name': '상담 에이전트',
        'en': 'Consulting Agent',
        'desc': '발명자와 대화하며 특허 작성에 필요한 핵심 정보를 수집합니다.',
        'detail': '대화 기반으로 발명의 문제점, 해결방법, 차별성, 기대효과를 정리합니다.',
        'inputs': ['발명 아이디어', '첨부 파일'],
        'outputs': ['상담 요약', '구조화된 발명 정보'],
        'steps': [],
        'active': True,
        'action_url': 'dashboard',
        'action_label': '대시보드로 이동',
    },
}


def agent_detail(request, slug):
    agent = AGENTS.get(slug)
    if not agent:
        from django.http import Http404
        raise Http404
    return render(request, 'pages/agent_detail.html', {'agent': agent, 'slug': slug})


def drawing_gallery(request):
    return render(request, 'pages/drawing_gallery.html')


def insights(request):
    return render(request, 'pages/insights.html')


QNA_SECTIONS = [
    {
        'id': 'basics',
        'section': '출원 기초',
        'en': 'Filing Basics',
        'items': [
            ('특허 출원이란 무엇인가요?', '발명을 특허청에 제출해 권리를 확보하는 절차입니다.'),
        ],
    },
]


def qna(request):
    total_count = sum(len(section['items']) for section in QNA_SECTIONS)
    return render(request, 'pages/qna.html', {
        'qna_sections': QNA_SECTIONS,
        'total_count': total_count,
    })
