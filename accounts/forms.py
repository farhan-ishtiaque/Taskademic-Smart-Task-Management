from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import UserProfile


class EmailUserCreationForm(forms.ModelForm):
    """Custom user creation form with email as username and additional profile fields"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm',
            'placeholder': 'Email address'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm',
            'placeholder': 'First name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm',
            'placeholder': 'Last name'
        })
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm',
            'placeholder': 'Password'
        })
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm',
            'placeholder': 'Confirm password'
        })
    )
    
    # UserProfile fields
    preferred_technique = forms.ChoiceField(
        choices=UserProfile.TECHNIQUE_CHOICES,
        required=False,
        initial='pomodoro',
        widget=forms.Select(attrs={
            'class': 'appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm'
        })
    )
    
    study_hours_per_day = forms.IntegerField(
        min_value=1,
        max_value=16,
        initial=4,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm',
            'placeholder': 'Study hours per day (1-16)'
        })
    )
    
    timezone = forms.CharField(
        max_length=50,
        initial='UTC',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm',
            'placeholder': 'Timezone (e.g., America/New_York, UTC)'
        })
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        return password2

    def save(self, commit=True):
        # Create user with email as username
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # Use email as username
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.set_password(self.cleaned_data['password1'])
        
        if commit:
            user.save()
            
            # Update UserProfile with additional fields
            profile = user.userprofile
            profile.preferred_technique = self.cleaned_data.get('preferred_technique', 'pomodoro')
            profile.study_hours_per_day = self.cleaned_data.get('study_hours_per_day', 4)
            profile.timezone = self.cleaned_data.get('timezone', 'UTC')
            profile.save()
            
        return user


class EmailAuthenticationForm(forms.Form):
    """Custom authentication form using email instead of username"""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm',
            'placeholder': 'Email address',
            'required': True,
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm',
            'placeholder': 'Password',
            'required': True
        })
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            try:
                # Find user by email
                user = User.objects.get(email=email)
                # Authenticate using the username (which is the email)
                self.user_cache = authenticate(
                    self.request, 
                    username=user.username, 
                    password=password
                )
                if self.user_cache is None:
                    raise forms.ValidationError("Invalid email or password.")
                else:
                    if not self.user_cache.is_active:
                        raise forms.ValidationError("This account is inactive.")
            except User.DoesNotExist:
                raise forms.ValidationError("Invalid email or password.")

        return self.cleaned_data

    def get_user(self):
        return getattr(self, 'user_cache', None)
