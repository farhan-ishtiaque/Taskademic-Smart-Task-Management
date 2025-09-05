from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserProfile


class EmailUserCreationForm(forms.ModelForm):
    """Custom user creation form with email as username and additional profile fields"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm',
            'placeholder': 'Email address'
        }),
        help_text='Enter a valid email address'
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm',
            'placeholder': 'First name'
        }),
        help_text='Enter your first name'
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm',
            'placeholder': 'Last name'
        }),
        help_text='Enter your last name'
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm',
            'placeholder': 'Password'
        }),
        help_text='Use at least 8 characters with a mix of letters, numbers, and symbols'
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm',
            'placeholder': 'Confirm password'
        }),
        help_text='Enter the same password as before, for verification'
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()  # Normalize email
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            try:
                validate_password(password1)
            except ValidationError as error:
                raise forms.ValidationError(error)
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        return password2

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            first_name = first_name.strip().title()  # Capitalize first letter
            if not first_name.replace(' ', '').isalpha():
                raise forms.ValidationError("First name should only contain letters.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            last_name = last_name.strip().title()  # Capitalize first letter
            if not last_name.replace(' ', '').isalpha():
                raise forms.ValidationError("Last name should only contain letters.")
        return last_name

    def save(self, commit=True):
        # Create user with email as username
        user = super().save(commit=False)
        user.username = self.cleaned_data['email'].lower()  # Use normalized email as username
        user.email = self.cleaned_data['email'].lower()
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.set_password(self.cleaned_data['password1'])
        
        if commit:
            user.save()
            
            # Ensure UserProfile exists with default values
            try:
                profile = user.userprofile
            except UserProfile.DoesNotExist:
                # Create profile manually if it doesn't exist
                profile = UserProfile.objects.create(user=user)
            
            # Set default values since these fields are not in the form
            profile.preferred_technique = 'pomodoro'
            profile.study_hours_per_day = 4
            profile.timezone = 'UTC'
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
        }),
        help_text='Enter your email address'
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm',
            'placeholder': 'Password',
            'required': True
        }),
        help_text='Enter your password'
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()  # Normalize email
        return email

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
