from django.contrib.auth.models import User
from django import forms

from models import Credential


class CredentialForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Credential
        fields = ("cluster", "username", "password1", "password2", "use_password")
