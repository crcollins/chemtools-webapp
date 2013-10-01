from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django import forms
from django.db import models

from Crypto.PublicKey import RSA

attributes = {"class": "required"}



class RegistrationForm(forms.Form):
    username = forms.RegexField(regex=r'^[\w.@+-]+$',
                                max_length=30,
                                widget=forms.TextInput(attrs=attributes),
                                label="Username",
                                error_message={'invalid': "This value may contain only letters, numbers and @.+- characters."}
                                )
    email = forms.EmailField()

    def clean_username(self):
        username = self.cleaned_data["username"]
        existing = User.objects.filter(username__iexact=username)
        if existing.exists():
            raise forms.ValidationError("A user with that username already exists.")
        elif username == "getkey":
            raise forms.ValidationError("That is not a valid username.")
        else:
            return self.cleaned_data["username"]


class SettingsForm(forms.Form):
    email = forms.EmailField()
    xsede_username = forms.CharField(max_length=50,
                                required=False,
                                label="XSEDE Username")
    new_ssh_keypair = forms.BooleanField(required=False)

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
    password_reset_key = models.CharField(max_length=40)
    reset_expires = models.DateTimeField(null=True, blank=True)


class UserProfileForm(forms.ModelForm):
    private_key = forms.CharField(widget=forms.Textarea)
    public_key = forms.CharField(widget=forms.Textarea)
    class Meta:
        model = UserProfile
        fields = ("xsede_username", "public_key", "activation_key", "password_reset_key", "reset_expires")


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)
