import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, UserSerializer
from .models import CustomUser

from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print('entering the loginView')
        email = request.data.get('email')
        password = request.data.get('password')
        
        print('email, password',email, password)
        user = authenticate(email=email, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)
    

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("Received request data:", request.data)

        token = request.data.get('token')
        if not token:
            return Response({'message': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch user info from Google API
        google_api_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
        headers = {'Authorization': f'Bearer {token}'}
        google_response = requests.get(google_api_url, headers=headers)

        if google_response.status_code != 200:
            return Response({'message': 'Invalid Google token'}, status=status.HTTP_400_BAD_REQUEST)

        user_data = google_response.json()
        email = user_data.get('email')
        full_name = user_data.get('name', '')  # Default empty string if not available
        profile_url = user_data.get('picture', '')

        print("Google user data:", user_data)

        # Check if user exists in DB
        user, created = CustomUser.objects.get_or_create(email=email, defaults={
            'full_name': full_name,
            'profile_url': profile_url
        })

        if not user.is_active:
            return Response({'message': 'You are blocked by admin'}, status=status.HTTP_403_FORBIDDEN)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)