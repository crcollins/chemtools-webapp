from django.conf.urls import patterns, url
from django.contrib import admin


admin.autodiscover()
molname = "\(\)A-Za-z0-9_\-"
multimolname = molname + ",\-\{\}\$\."

urlpatterns = patterns('chem.views',
    url(r'^$', "index", name="chem_index"),
    url(r'^multi_job/$', "multi_job", name="multi_job"),
    url(r"^upload/$", "upload_data", name="upload"),

    url(r"^(?P<molecule>[%s]*)/$" % molname, "molecule_detail", name="mol_detail"),
    url(r"^(?P<molecule>[%s]*)\.json$" % molname, "molecule_detail_json", name="mol_json"),
    url(r"^(?P<molecule>[%s]*)\.gjf$" % molname, "write_gjf", name="mol_gjf"),
    url(r"^(?P<molecule>[%s]*)\.mol2$" % molname, "write_mol2", name="mol_mol2"),
    url(r"^(?P<molecule>[%s]*)\.png$" % molname, "write_png", name="mol_png"),
    url(r"^(?P<molecule>[%s]*)\.svg$" % molname, "write_svg", name="mol_svg"),
    url(r"^(?P<molecule>[%s]*)/report/$" % molname, "report", name="mol_report"),

    url(r"^(?P<string>[%s]*)/$" % multimolname, "multi_molecule", name="multi_mol"),
    url(r"^(?P<string>[%s]*)\.zip$" % multimolname, "multi_molecule_zip", name="mol_zip"),

    url(r"^(?P<string>[%s]*)/check/$" % multimolname, "molecule_check", name="mol_check"),
)

