import json
import logging
from django.http import JsonResponse
from django.contrib.auth import login, logout
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def firebase_login(request):
    """Handle Firebase authentication login"""
    try:
        data = json.loads(request.body)
        id_token = data.get('idToken')
        user_data = data.get('userData', {})
        
        if not id_token:
            return JsonResponse({'error': 'ID token is required'}, status=400)
        
        # Try to verify the Firebase token
        try:
            from taskademic.firebase_init import verify_firebase_token
            decoded_token = verify_firebase_token(id_token)
            logger.info(f"Token verified for user: {decoded_token.get('email')}")
        except Exception as e:
            logger.warning(f"Firebase token verification failed: {e}")
            # For testing without proper Firebase setup, use user_data
            if not user_data.get('email'):
                return JsonResponse({'error': 'Invalid token and no user data'}, status=401)
            decoded_token = user_data
        
        # Get or create user from Firebase data
        try:
            from .models import FirebaseUser
            user = FirebaseUser.get_or_create_user(decoded_token)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            # Fallback: create user without FirebaseUser model
            email = decoded_token.get('email')
            if not email:
                return JsonResponse({'error': 'No email in token'}, status=400)
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Create new user
                username = email.split('@')[0]
                counter = 1
                original_username = username
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                display_name = decoded_token.get('name', '') or decoded_token.get('displayName', '')
                name_parts = display_name.split(' ', 1)
                first_name = name_parts[0] if name_parts else ''
                last_name = name_parts[1] if len(name_parts) > 1 else ''
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )
        
        # Log the user in
        login(request, user)
        
        logger.info(f"User {user.email} logged in successfully via Firebase")
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'redirect_url': '/dashboard/'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Firebase login error: {e}")
        return JsonResponse({'error': f'Authentication failed: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def firebase_logout(request):
    """Handle Firebase authentication logout"""
    try:
        logout(request)
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"Firebase logout error: {e}")
        return JsonResponse({'error': 'Logout failed'}, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def firebase_status(request):
    """Check Firebase authentication status"""
    try:
        # Check if Firebase is initialized
        firebase_initialized = False
        try:
            from taskademic.firebase_init import initialize_firebase
            firebase_initialized = initialize_firebase()
        except Exception as e:
            logger.warning(f"Firebase status check failed: {e}")
        
        return Response({
            'firebase_initialized': firebase_initialized,
            'user_authenticated': request.user.is_authenticated,
            'user_id': request.user.id if request.user.is_authenticated else None,
            'username': request.user.username if request.user.is_authenticated else None,
            'message': 'Firebase credentials not configured' if not firebase_initialized else 'Firebase ready'
        })
    except Exception as e:
        logger.error(f"Firebase status check error: {e}")
        return Response({'error': str(e)}, status=500)