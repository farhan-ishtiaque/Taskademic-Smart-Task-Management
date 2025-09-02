from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    total_points = serializers.IntegerField(source='userprofile.total_points', read_only=True)
    level = serializers.IntegerField(source='userprofile.level', read_only=True)
    preferred_technique = serializers.CharField(source='userprofile.preferred_technique', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'date_joined', 'total_points', 'level', 'preferred_technique']
        read_only_fields = ['id', 'username', 'date_joined']


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """API endpoint for user registration"""
    try:
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        preferred_technique = request.data.get('preferred_technique', 'pomodoro')
        
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
            
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)
            
        user = User.objects.create_user(
            username=username, 
            email=email, 
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Update user profile with preferred technique
        profile = user.userprofile
        profile.preferred_technique = preferred_technique
        profile.save()
        
        return Response({
            'message': 'User created successfully',
            'user_id': user.id,
            'username': user.username
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """API endpoint for user login"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    if user:
        login(request, user)
        serializer = UserProfileSerializer(user)
        return Response({
            'message': 'Login successful',
            'user': serializer.data
        }, status=status.HTTP_200_OK)
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """API endpoint for user logout"""
    logout(request)
    return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get current user profile"""
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats(request):
    """Get user statistics"""
    profile = request.user.userprofile
    from tasks.models import Task
    
    total_tasks = Task.objects.filter(user=request.user).count()
    completed_tasks = Task.objects.filter(user=request.user, status='done').count()
    pending_tasks = Task.objects.filter(user=request.user, status__in=['todo', 'in_progress']).count()
    
    return Response({
        'total_points': profile.total_points,
        'level': profile.level,
        'streak_count': profile.streak_count,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    })


def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            login(request, user)
            return redirect('dashboard:home')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard:home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')


def logout_view(request):
    """User logout view"""
    logout(request)
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """User profile view"""
    from tasks.models import Task
    
    # Get task counts for the user
    completed_tasks_count = Task.objects.filter(user=request.user, status='done').count()
    in_progress_tasks_count = Task.objects.filter(user=request.user, status='in_progress').count()
    total_tasks_count = Task.objects.filter(user=request.user).count()
    
    context = {
        'completed_tasks_count': completed_tasks_count,
        'in_progress_tasks_count': in_progress_tasks_count,
        'total_tasks_count': total_tasks_count,
    }
    
    return render(request, 'accounts/profile.html', context)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile_api(request):
    """API endpoint for user profile"""
    if request.method == 'GET':
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
