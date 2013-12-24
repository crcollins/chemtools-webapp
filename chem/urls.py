from django.conf.urls import patterns, url

from django.contrib import admin
admin.autodiscover()

molname = "A-Za-z0-9_\-"
multimolname = molname + ",\-\{\}\$\."

urlpatterns = patterns('chem.views',
    url(r'^$', "index", name="chem_index"),
    url(r'^multi_job/$', "multi_job", name="multi_job"),

    url(r"^(?P<molecule>[%s]*)/$" % molname, "molecule_detail"),
    url(r"^(?P<molecule>[%s]*)\.json$" % molname, "molecule_detail_json"),
    url(r"^(?P<molecule>[%s]*)\.gjf$" % molname, "write_gjf"),
    url(r"^(?P<molecule>[%s]*)\.mol2$" % molname, "write_mol2"),
    url(r"^(?P<molecule>[%s]*)\.png$" % molname, "write_png"),
    url(r"^(?P<molecule>[%s]*)/report/$" % molname, "report"),

    url(r"^(?P<string>[%s]*)/$" % multimolname, "multi_molecule"),
    url(r"^(?P<string>[%s]*)\.zip$" % multimolname, "multi_molecule_zip"),

    url(r"^(?P<string>[%s]*)/check/$" % multimolname, "molecule_check"),
)
