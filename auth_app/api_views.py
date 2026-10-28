# auth_app/api_views.py
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer

# Registro API
@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            "username": user.username,
            "email": user.email
        }, status=201)
    return Response(serializer.errors, status=400)

# Login: usando SimpleJWT
class MyTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

# Renovación token
@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    try:
        refresh = RefreshToken(request.data.get('refresh'))
        return Response({
            "access": str(refresh.access_token)
        }, status=200)
    except Exception as e:
        return Response({"error": "Token inválido"}, status=400)
