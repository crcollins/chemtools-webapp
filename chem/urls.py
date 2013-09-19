from django.conf.urls import patterns, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('chem.views',
    url(r'^$', "index"),

    url(r"^jobs/$", "job_index"),
    url(r"^jobs.json$", "get_job_list"),
    url(r"^jobs/(?P<jobid>[0-9]*)/$", "job_detail"),
    url(r"^jobs/(?P<jobid>[0-9]*)/reset/$", "reset_job"),
    url(r"^jobs/(?P<jobid>[0-9]*)/kill/$", "kill_job"),

    url(r"^(?P<molecule>[A-Za-z0-9_]*)/$", "gen_detail"),
    url(r"^(?P<molecule>[A-Za-z0-9_]*)\.gjf$", "write_gjf"),
    url(r"^(?P<molecule>[A-Za-z0-9_]*)\.mol2$", "write_mol2"),
    url(r"^(?P<molecule>[A-Za-z0-9_]*)\.png$", "write_png"),
    url(r"^(?P<molecule>[A-Za-z0-9_]*)/report/$", "report"),

    url(r"^(?P<string>[A-Za-z0-9_,\{\}\$]*)/$", "gen_multi_detail"),
    url(r"^(?P<string>[A-Za-z0-9_,\{\}\$]*)\.zip$", "gen_multi_detail_zip"),

    url(r"^(?P<string>[A-Za-z0-9_,\{\}\$]*)/check/$", "molecule_check"),
)
