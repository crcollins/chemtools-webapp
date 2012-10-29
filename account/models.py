from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django import forms
from django.db import models


attributes = {"class": "required"}

class RegistrationForm(forms.Form):
    username = forms.RegexField(regex=r'^[\w.@+-]+$',
                                max_length=30,
                                widget=forms.TextInput(attrs=attributes),
                                label="Username",
                                error_message={'invalid': "This value may contain only letters, numbers and @.+- characters."}
                                )
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=attributes,
                                render_value=False),
                                label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=attributes,
                                render_value=False),
                                label="Password (again)")

    def clean_username(self):
        existing = User.objects.filter(username__iexact=self.cleaned_data["username"])
        if existing.exists():
            raise forms.ValidationError("A user with that username already exists.")
        else:
            return self.cleaned_data["username"]

    def clean(self):
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError("The two password fields did not match.")
        return self.cleaned_data

class SettingsForm(forms.Form):
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=attributes,
                                render_value=False),
                                label="Password",
                                required=False)
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=attributes,
                                render_value=False),
                                label="Password (again)",
                                required=False)

    def clean(self):
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError("The two password fields did not match.")
        return self.cleaned_data


class UserProfile(models.Model):
    user = models.OneToOneField(User)

    xsede_username = models.CharField(max_length=50)
    private_key = models.CharField(max_length=2048)
    public_key = models.CharField(max_length=512)

    activation_key = models.CharField(max_length=40)

class UserProfileForm(forms.ModelForm):
    private_key = forms.CharField(widget=forms.Textarea)
    public_key = forms.CharField(widget=forms.Textarea)
    class Meta:
        model = UserProfile
        fields = ("xsede_username", "private_key", "public_key", "activation_key")

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)