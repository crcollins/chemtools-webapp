from django.db import models
from django import forms
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from project.utils import get_ssh_connection, get_sftp_connection, StringIO, \
    AESCipher


class Cluster(models.Model):
    name = models.CharField(max_length=50)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='clusters', null=True)
    hostname = models.CharField(max_length=255)
    port = models.IntegerField(default=22)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.full_hostname())

    def full_hostname(self):
        return "%s:%d" % (self.hostname, self.port)

    def get_long_name(self):
        if self.creator:
            return "%s:%s:%d" % (self.creator.username, self.full_hostname(), self.id)
        else:
            return "%s:%d" % (self.full_hostname(), self.id)

    @classmethod
    def get_clusters(cls, user):
        if user is not None:
            return Cluster.objects.filter(Q(creator=user) | Q(creator__isnull=True))
        else:
            return Cluster.objects.filter(creator__isnull=True)


class ClusterForm(forms.ModelForm):

    class Meta:
        model = Cluster
        fields = ("name", "hostname", "port")

    def __init__(self, user, *args, **kwargs):
        super(ClusterForm, self).__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        if Cluster.objects.filter(creator=self.user, **self.cleaned_data):
            forms.ValidationError("That cluster already exists")
        return self.cleaned_data


class EncryptedCharField(models.CharField):
    cipher = AESCipher()
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if value is None:
            return value
        if value.startswith("$AES$"):
            return self.cipher.decrypt(value[len("$AES$"):])
        # Warning: This strips all unicode chars. This is a hack because I
        # can not figure out how to get the validation to work right...
        return value.encode('ascii', 'ignore')

    def get_prep_value(self, value):
        return "$AES$" + self.cipher.encrypt(value)


class Credential(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='credentials')

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
            user = type(self.user).objects.get(id=self.user.id)
            private = StringIO(user.private_key)
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
            private = StringIO(self.user.private_key)
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
    UNKNOWN = 'U'
    KILLED = 'K'
    FAILED = 'F'
    WALLTIME = 'W'
    QUEUED = 'Q'
    RUNNING = 'R'
    COMPLETED = 'C'
    MISSING = 'M'
    JOB_STATES = (
        (UNKNOWN, "Unknown"),  # If the job falls out of the queue before check
        (KILLED, "Killed"),
        (FAILED, "Failed"),
        (WALLTIME, "Walltime"),
        (QUEUED, "Queued"),
        (RUNNING, "Running"),
        (COMPLETED, "Completed"),
        (MISSING, "Missing"),
    )
    RUNNING_STATES = set((
        QUEUED,
        RUNNING,
    ))
    POST_STATES = set((
        UNKNOWN,
        KILLED,
        FAILED,
        WALLTIME,
        COMPLETED,
        MISSING,
    ))

    credential = models.ForeignKey(Credential)
    name = models.CharField(max_length=400)
    jobid = models.CharField(max_length=400)

    keywords = models.CharField(max_length=200, null=True, blank=True)
    memory = models.IntegerField(null=True, blank=True)
    nprocshared = models.IntegerField(null=True, blank=True)
    charge = models.IntegerField(null=True, blank=True)
    multiplicity = models.IntegerField(null=True, blank=True)

    molecule = models.CharField(max_length=400, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    nodes = models.IntegerField(null=True, blank=True)
    walltime = models.IntegerField(null=True, blank=True)
    allocation = models.CharField(max_length=20, null=True, blank=True)
    template = models.TextField(null=True, blank=True)

    state = models.CharField(max_length=1, choices=JOB_STATES, default=QUEUED)
    created = models.DateTimeField(auto_now=True)
    started = models.DateTimeField(auto_now=False, null=True)
    last_update = models.DateTimeField(auto_now=True)
    ended = models.DateTimeField(auto_now=False, null=True)

    def __init__(self, *args, **kwargs):
        fields = set([x.name for x in Job._meta.fields])
        newkwargs = {k: v for k, v in kwargs.items() if k in fields}
        super(Job, self).__init__(*args, **newkwargs)

    def __unicode__(self):
        return "%s - %s - %s" % (self.credential, self.jobid, self.state)

    @classmethod
    def get_running_jobs(cls, credential=None, user=None):
        if user is not None:
            return Job.objects.filter(credential__user=user,
                                      state__in=cls.RUNNING_STATES)
        elif credential is not None:
            return Job.objects.filter(credential=credential,
                                      state__in=cls.RUNNING_STATES)
        else:
            return Job.objects.filter(state__in=cls.RUNNING_STATES)

    @classmethod
    def get_oldest_update_time(cls, **kwargs):
        jobs = Job.get_running_jobs(**kwargs)
        if jobs:
            return jobs.order_by("last_update")[0].last_update
        else:
            return timezone.now()

    @classmethod
    def _update_states(cls, credential, jobids, state, now):
        update = {
            "state": state.upper(),
            "last_update": now,
        }
        if state in cls.POST_STATES:
            update["ended"] = now
        jobs = Job.objects.filter(credential=credential, jobid__in=jobids)
        jobs.update(**update)

        if state == cls.RUNNING or state in cls.POST_STATES:
            jobs.filter(started=None).update(started=now)

    @classmethod
    def update_states(cls, credential, state_ids):
        now = timezone.now()
        for state, jobids in state_ids.items():
            Job._update_states(credential, jobids, state, now)

    def format(self):
        if self.started:
            t = self.last_update - self.started
            hours, remainder = divmod(t.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            runtime = "%02d:%02d" % (hours, minutes)
        else:
            runtime = '--'
        return (
            self.jobid,
            self.credential.username,
            self.name,
            self.memory,
            self.walltime,
            runtime,
            self.state,
        )
