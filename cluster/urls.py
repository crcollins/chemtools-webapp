from django.conf.urls import patterns, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('cluster.views',
    url(r"^$", "job_index"),
    url(r"^running.json$", "get_job_list"),
    url(r"^creds/$", "cred_index"),
    url(r"^(?P<jobid>[0-9]*)/$", "job_detail"),
    url(r"^(?P<jobid>[0-9]*)/reset/$", "reset_job"),
    url(r"^(?P<jobid>[0-9]*)/kill/$", "kill_job"),
)
