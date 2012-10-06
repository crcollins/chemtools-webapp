from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('chem.views',
    url(r'^$', "index"),
    url(r"^frag/$", "frag_index"),
    url(r"^frag/(?P<frag>[A-Za-z0-9]*)/$", "get_frag"),

    url(r"^upload/$", "upload_data"),
    url(r"^jobs/$", "job_index"),
    url(r"^jobs/(?P<jobid>[0-9]*)/$", "job_detail"),
    url(r"^jobs/(?P<jobid>[0-9]*)/reset/$", "reset_job"),
    url(r"^jobs/(?P<jobids>[0-9,]*)/$", "job_multi_detail"),

    url(r"^(?P<molecule>[A-Za-z0-9_]*)/$", "gen_detail"),
    url(r"^(?P<molecule>[A-Za-z0-9_]*)\.gjf$", "write_gjf"),
    url(r"^(?P<molecule>[A-Za-z0-9_]*)\.mol2$", "write_mol2"),
    url(r"^(?P<molecule>[A-Za-z0-9_]*)\.png$", "write_png"),
    url(r"^(?P<molecule>[A-Za-z0-9_]*)/report/$", "report"),
    url(r"^(?P<molecule>[A-Za-z0-9_]*)/job/$", "get_job"),

    url(r"^(?P<molecules>[A-Za-z0-9_,]*)/$", "gen_multi_detail"),
    url(r"^(?P<molecules>[A-Za-z0-9_,]*)\.zip$", "gen_multi_detail_zip"),

    url(r"^(?P<molecule>[A-Za-z0-9_]*)/job/run/$", "run_molecule"),
)

