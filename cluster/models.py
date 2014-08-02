from django.contrib.auth.models import User
from django.db import models
from django import forms

from project.utils import get_ssh_connection, get_sftp_connection, StringIO, \
                        AESCipher


class Cluster(models.Model):
    name = models.CharField(max_length=50)
    hostname = models.CharField(max_length=255)
    port = models.IntegerField(default=22)

    def __unicode__(self):
        return "%s (%s:%d)" % (self.name, self.hostname, self.port)


class ClusterForm(forms.ModelForm):
    class Meta:
        model = Cluster
        fields = ("name", "hostname", "port")


class EncryptedCharField(models.CharField):
    cipher = AESCipher()
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if value is not None and value.startswith("$AES$"):
            return self.cipher.decrypt(value[len("$AES$"):])
        else:
            return value

    def get_prep_value(self, value):
        return "$AES$" + self.cipher.encrypt(value)


class Credential(models.Model):
    user = models.ForeignKey(User, related_name='credentials')

    cluster = models.ForeignKey(Cluster)
    username = models.CharField(max_length=255, null=True, blank=True)
    password = EncryptedCharField(max_length=255, null=True, blank=True)
    use_password = models.BooleanField(default=False)

    def __unicode__(self):
        return "%s@%s:%d" % (self.username, self.cluster.hostname,
                            self.cluster.port)

    def get_long_name(self):
        return "%s-%d" % (unicode(self), self.id)

    def get_ssh_connection(self):
        if self.use_password:
            return get_ssh_connection(self.cluster.hostname,
                                    self.username,
                                    password=self.password,
                                    port=self.cluster.port)
        else:
            try:
                del self.user._profile_cache
            except:
                pass
            profile = self.user.get_profile()
            private = StringIO(profile.private_key)
            return get_ssh_connection(self.cluster.hostname,
                                    self.username,
                                    key=private,
                                    port=self.cluster.port)

    def get_sftp_connection(self):
        if self.use_password:
            return get_sftp_connection(self.cluster.hostname,
                                    self.username,
                                    password=self.password,
                                    port=self.cluster.port)
        else:
            try:
                del self.user._profile_cache
            except:
                pass
            profile = self.user.get_profile()
            private = StringIO(profile.private_key)
            return get_sftp_connection(self.cluster.hostname,
                                    self.username,
                                    key=private,
                                    port=self.cluster.port)

    def connection_works(self):
        try:
            self.get_ssh_connection()
            return True
        except Exception:
            return False


class CredentialAdminForm(forms.ModelForm):
    password = forms.CharField(max_length=50, required=False,
                            widget=forms.PasswordInput)
    password2 = forms.CharField(max_length=50, required=False,
                            widget=forms.PasswordInput)

    class Meta:
        model = Credential
        fields = ("user", "cluster", "username", "password",
                "password2", "use_password")

    def clean_use_password(self):
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        use_password = self.cleaned_data.get("use_password")

        if not use_password:
            return False
        if password != password2:
            raise forms.ValidationError("Your passwords do not match")
        return True


class CredentialForm(CredentialAdminForm):
    class Meta:
        model = Credential
        fields = ("cluster", "username", "password",
                "password2", "use_password")

    def __init__(self, user, *args, **kwargs):
        super(CredentialForm, self).__init__(*args, **kwargs)
        self.user = user


class Job(models.Model):
    UNKNOWN = -4
    KILLED = -3
    FAILED = -2
    WALLTIME = -1
    QUEUED = 0
    RUNNING = 1
    COMPLETED = 2
    JOB_STATES = (
        (UNKNOWN, "Uknown"),  # If the job falls out of the queue before check
        (KILLED, "Killed"),
        (FAILED, "Failed"),
        (WALLTIME, "Walltime"),
        (QUEUED, "Queued"),
        (RUNNING, "Running"),
        (COMPLETED, "Completed"),
    )
    credential = models.ForeignKey(Credential)

    keywords = models.CharField(max_length=200)
    memory = models.IntegerField()
    nprocshared = models.IntegerField()
    charge = models.IntegerField()
    multiplicity = models.IntegerField()

    molecule = models.CharField(max_length=400)
    name = models.CharField(max_length=400)
    email = models.EmailField()
    nodes = models.IntegerField()
    walltime = models.IntegerField()
    allocation = models.CharField(max_length=20)
    template = models.TextField()

    jobid = models.CharField(max_length=400)
    state = models.IntegerField(choices=JOB_STATES, default=QUEUED)
    created = models.DateTimeField(auto_now=True)
    started = models.DateTimeField(auto_now=False, null=True)
    last_update = models.DateTimeField(auto_now=True)
    ended = models.DateTimeField(auto_now=False, null=True)

    def __init__(self, *args, **kwargs):
        fields = set([x.name for x in Job._meta.fields])
        newkwargs = {k: v for k, v in kwargs.items() if k in fields}
        super(Job, self).__init__(*args, **newkwargs)

    @classmethod
    def get_running_jobs(cls, credential):
        return Job.objects.filter(credential=credential,
                                state__in=[QUEUED, RUNNING])

    @classmethod
    def _update_states(cls, credential, jobids, state):
        Job.objects.filter(credential=credential, jobid__in=jobids).update(state=state)

    @classmethod
    def update_states(cls, credential, state_ids):
        for state, jobids in state_ids.items():
            Job._update_states(credential, jobids, state)
