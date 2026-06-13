from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import SignupSerializer, LoginSerializer, UserSerializer, ProfileUpdateSerializer

User = get_user_model()


def get_tokens_for_user(user):
    """유저 객체로 JWT 토큰 쌍 생성"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access':  str(refresh.access_token),
    }


class SignupAPIView(APIView):
    """
    POST /api/auth/signup/
    회원가입 + JWT 토큰 발급

    Request Body (JSON):
        username, name, gender, age, password, password2

    Response:
        201 Created → { user: {...}, access, refresh }
        400 Bad Request → { errors }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # 가입 직후 is_login = True
            user.is_login = True
            user.save(update_fields=['is_login'])
            tokens = get_tokens_for_user(user)
            return Response(
                {
                    'message': '회원가입이 완료되었습니다.',
                    'user': UserSerializer(user).data,
                    **tokens,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    """
    POST /api/auth/login/
    로그인 + JWT 토큰 발급

    Request Body (JSON):
        username, password

    Response:
        200 OK → { user: {...}, access, refresh }
        401 Unauthorized → { error }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {'error': '아이디 또는 비밀번호가 올바르지 않습니다.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return Response(
                {'error': '비활성화된 계정입니다.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # is_login = True 업데이트
        user.is_login = True
        user.save(update_fields=['is_login'])

        tokens = get_tokens_for_user(user)
        return Response(
            {
                'message': f'{user.name}님, 환영합니다.',
                'user': UserSerializer(user).data,
                **tokens,
            },
            status=status.HTTP_200_OK,
        )


class LogoutAPIView(APIView):
    """
    POST /api/auth/logout/
    로그아웃 - 리프레시 토큰 블랙리스트 처리

    Headers:
        Authorization: Bearer <access_token>

    Request Body (JSON):
        refresh: <refresh_token>

    Response:
        200 OK → { message }
        400 Bad Request → { error }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'refresh 토큰이 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()   # 토큰 블랙리스트 등록
        except TokenError:
            return Response(
                {'error': '유효하지 않거나 이미 만료된 토큰입니다.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # is_login = False 업데이트
        request.user.is_login = False
        request.user.save(update_fields=['is_login'])

        return Response({'message': '로그아웃되었습니다.'}, status=status.HTTP_200_OK)


class MeAPIView(APIView):
    """
    GET /api/auth/me/
    현재 로그인한 유저 정보 조회

    Headers:
        Authorization: Bearer <access_token>

    Response:
        200 OK → { user: {...} }
        401 Unauthorized
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {'user': UserSerializer(request.user).data},
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'user': UserSerializer(request.user).data},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
