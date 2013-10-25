from django.contrib.auth.models import User
from django.db import models
from django import forms

from project.utils import get_ssh_connection, get_sftp_connection, StringIO, AESCipher
from chemtools.utils import CLUSTER_TUPLES


class Job(models.Model):
    molecule = models.CharField(max_length=400)
    name = models.CharField(max_length=400)
    email = models.EmailField()
    cluster = models.CharField(max_length=1, choices=CLUSTER_TUPLES)
    nodes = models.IntegerField()
    walltime = models.IntegerField()
    allocation = models.CharField(max_length=20)
    jobid = models.CharField(max_length=400)
    created = models.DateTimeField(auto_now=True)
    started = models.DateTimeField(auto_now=False, null=True)
    ended = models.DateTimeField(auto_now=False, null=True)


class Cluster(models.Model):
    name = models.CharField(max_length=50)
    hostname = models.CharField(max_length=255)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.hostname)


class EncryptedCharField(models.CharField):
    cipher = AESCipher()
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if value is not None and value.startswith("$AES$"):
            return self.cipher.decrypt(value[len("$AES$"):])
        else:
            return value

    def get_prep_value(self, value):
        return "$AES$"+self.cipher.encrypt(value)


class Credential(models.Model):
    user = models.ForeignKey(User, related_name='credentials')

    cluster = models.ForeignKey(Cluster)
    username = models.CharField(max_length=255, null=True, blank=True)
    password = EncryptedCharField(max_length=255, null=True, blank=True)
    use_password = models.BooleanField(default=False)

    def get_ssh_connection(self):
        if self.use_password:
            return get_ssh_connection(self.cluster.hostname, self.username, password=self.password)
        else:
            profile = self.user.get_profile()
            private = StringIO(profile.private_key)
            return get_ssh_connection(self.cluster.hostname, self.username, key=private)

    def get_sftp_connection(self):
        if self.use_password:
            return get_sftp_connection(self.cluster.hostname, self.username, password=self.password)
        else:
            profile = self.user.get_profile()
            private = StringIO(profile.private_key)
            return get_sftp_connection(self.cluster.hostname, self.username, key=private)


class CredentialForm(forms.ModelForm):
    password = forms.CharField(max_length=50, required=False, widget=forms.PasswordInput)
    password2 = forms.CharField(max_length=50, required=False, widget=forms.PasswordInput)

    class Meta:
        model = Credential
        fields = ("cluster", "username", "password", "password2", "use_password")

    def clean_use_password(self):
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        use_password = self.cleaned_data.get("use_password")

        if not use_password:
            return False
        if password != password2:
            raise forms.ValidationError("Your passwords do not match")
        return True