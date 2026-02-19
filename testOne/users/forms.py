from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'document_number', 'role')

class CustomUserChangeForm(UserChangeForm):
    password = None  # Prevent password change here, use separate form if needed
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'document_number', 'role')

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email')

class UserSignatureForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('digital_signature',)
        widgets = {
            'digital_signature': forms.HiddenInput()
        }

class AdminResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        label="Nueva Contraseña", 
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Ingrese la nueva contraseña para este usuario."
    )
    confirm_password = forms.CharField(
        label="Confirmar Contraseña", 
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data
