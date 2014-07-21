from django.contrib.auth.models import User
from django import forms

from account.models import UserProfile


attributes = {"class": "required"}


class RegistrationForm(forms.Form):
    username = forms.RegexField(
                regex=r'^[\w.@+-]+$',
                max_length=30,
                widget=forms.TextInput(attrs=attributes),
                label="Username",
                error_message={
                'invalid': "This value may contain only \
                            letters, numbers and @.+- characters."}
                )
    email = forms.EmailField()

    def clean_username(self):
        username = self.cleaned_data["username"]
        existing = User.objects.filter(username__iexact=username)
        if existing.exists():
            raise forms.ValidationError("A user with that \
                                        username already exists.")
        else:
            return self.cleaned_data["username"]


class SettingsForm(forms.Form):
    email = forms.EmailField()
    xsede_username = forms.CharField(max_length=50,
                                required=False,
                                label="XSEDE Username")
    new_ssh_keypair = forms.BooleanField(required=False)
    public_key = forms.CharField(required=False, widget=forms.Textarea(attrs={"cols": 50, "rows": 6}))


class UserProfileForm(forms.ModelForm):
    private_key = forms.CharField(widget=forms.Textarea)
    public_key = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = UserProfile
        fields = ("xsede_username", "public_key", "activation_key",
                    "password_reset_key", "reset_expires")
