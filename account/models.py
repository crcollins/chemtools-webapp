from django.contrib.auth.models import User
from django import forms


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