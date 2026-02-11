from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'document_number')

class CustomUserChangeForm(UserChangeForm):
    password = None  # Prevent password change here, use separate form if needed
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'document_number')
