import requests
import logging
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
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
        if user.is_staff:
            return Response({'message': 'Admin login required'}, status=status.HTTP_403_FORBIDDEN)

        if not user.is_active:
            return Response({'message': 'You are blocked by admin'}, status=status.HTTP_403_FORBIDDEN)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
    

class UserListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer
    queryset = CustomUser.objects.all().order_by('-date_joined')

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer
    queryset = CustomUser.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_superuser:
            return Response(
                {"error": "Cannot delete superuser accounts"},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_superuser and not request.user.is_superuser:
            return Response(
                {"error": "Only superusers can modify superuser accounts"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)



logger = logging.getLogger(__name__)

class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get('refresh', '')
            logger.info(f"Refresh token received: {refresh_token[:10]}...")

            response = super().post(request, *args, **kwargs)
            
            logger.info("Token refresh successful")
            return response

        except TokenError as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return Response({
                'error': 'Invalid refresh token',
                'detail': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        except Exception as e:
            logger.error(f"Unexpected error in token refresh: {str(e)}")
            return Response({
                'error': 'Token refresh failed',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ToggleUserActiveStatusView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):

        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'User ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        user.is_active = not user.is_active
        user.save()

        return Response({'message': 'User status updated successfully'}, status=status.HTTP_200_OK)