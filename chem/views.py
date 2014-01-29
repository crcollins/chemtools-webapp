from cStringIO import StringIO
import os
import urllib
import time

from django.shortcuts import render, redirect
from django.template import Context
from django.http import HttpResponse, HttpResponseRedirect
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.utils import simplejson

from models import ErrorReport, ErrorReportForm, JobForm

from chemtools import gjfwriter
from chemtools.utils import write_job
from chemtools.ml import get_properties_from_feature_vector, get_properties_from_feature_vector2, get_feature_vector, get_feature_vector2
from chemtools.mol_name import name_expansion, get_exact_name
from chemtools.constants import KEYWORDS
from chemtools.interface import get_multi_molecule, get_multi_job
import cluster.interface
from data.models import DataPoint


def index(request):
    if request.GET.get("molecule"):

        func = molecule_detail
        if set(",{}$") & set(request.GET.get("molecule")):
            func = multi_molecule

        params = {"keywords": request.GET.get("keywords", None)}
        if params["keywords"] != KEYWORDS:
            url = "%s?%s" % (reverse(func, args=(request.GET.get("molecule"), )),
                urllib.urlencode(params))
            return HttpResponseRedirect(url)
        else:
            return redirect(func, request.GET.get("molecule"))
    return render(request, "chem/index.html")


###########################################################
###########################################################
# Generation Stuff
###########################################################
###########################################################

def _get_molecule_warnings(string):
    errors = []
    warnings = []
    molecules = name_expansion(string)
    start = time.time()
    for mol in molecules:
        if time.time() - start > 1:
            raise ValueError("The operation has timed out.")
        try:
            gjfwriter.parse_name(mol)
            errors.append(None)
        except Exception as e:
            errors.append(str(e))
        warn = ErrorReport.objects.filter(molecule=mol)
        warnings.append(True if warn else None)
    return molecules, warnings, errors


def _get_molecule_info(request, molecule):
    _, warnings, errors = _get_molecule_warnings(molecule)
    keywords = request.REQUEST.get("keywords", KEYWORDS)

    if not errors[0]:
        exactspacer = get_exact_name(molecule, spacers=True)
        exactname = exactspacer.replace('*', '')
        features = [get_feature_vector(exactspacer), get_feature_vector2(exactspacer)]
        homo, lumo, gap = get_properties_from_feature_vector(features[1])
        temp = DataPoint.objects.filter(exact_name=exactname, band_gap__isnull=False)
        if temp:
            datapoint = temp[0]
        else:
            datapoint = None
    else:
        exactname = ''
        exactspacer = ''
        features = ['', '']
        homo, lumo, gap = None, None, None

    a = {
        "molecule": molecule,
        "exact_name": exactname,
        "exact_name_spacers": exactspacer,
        "features": features,
        "homo": homo,
        "lumo": lumo,
        "band_gap": gap,
        "known_errors": warnings[0],
        "error_message": errors[0],
        "keywords": keywords,
        }
    return a


def multi_job(request):
    form = JobForm.get_form(request, "{{ name }}")

    c = Context({
        "form": form,
        })
    if not form.is_valid():
        return render(request, "chem/multi_job.html", c)

    d = dict(form.cleaned_data)
    if request.method == "GET":
        string = request.REQUEST.get('filenames', '').replace('\n', ',')

        ret_zip = get_multi_job(string, form)

        response = HttpResponse(ret_zip, mimetype="application/zip")
        response["Content-Disposition"] = "attachment; filename=output.zip"
        return response
    elif request.method == "POST":
        cred = d.pop("credential")
        files = request.FILES.getlist("files")
        strings = [''.join(f.readlines()) for f in files]
        names = [os.path.splitext(f.name)[0] for f in files]
        a = cluster.interface.run_jobs(cred, names, strings, **d)
        return HttpResponse(simplejson.dumps(a), mimetype="application/json")
    else:
        return render(request, "chem/multi_job.html", c)


def molecule_check(request, string):
    a = {
        "error": None,
        "molecules": [[x] for x in name_expansion(string)]
    }
    try:
        molecules, warnings, errors = _get_molecule_warnings(string)
        a["molecules"] = zip(molecules, warnings, errors)
    except ValueError:
        a["error"] = "The operation timed out."
        a["molecules"] = None
    return HttpResponse(simplejson.dumps(a), mimetype="application/json")


def molecule_detail(request, molecule):
    form = JobForm.get_form(request, molecule)
    keywords = request.REQUEST.get("keywords", '')
    add = "" if request.GET.get("view") else "attachment; "

    if form.is_valid():
        d = dict(form.cleaned_data)
        if request.method == "GET":
            response = HttpResponse(write_job(**d), content_type="text/plain")
            response['Content-Disposition'] = add + 'filename=%s.job' % molecule
            return response
        elif request.method == "POST":
            d["keywords"] = keywords
            cred = d.pop("credential")
            a = cluster.interface.run_standard_job(cred, molecule, **d)
            return HttpResponse(simplejson.dumps(a), mimetype="application/json")
    a = _get_molecule_info(request, molecule)
    a["form"] = form
    c = Context(a)
    return render(request, "chem/molecule_detail.html", c)


def molecule_detail_json(request, molecule):
    a = _get_molecule_info(request, molecule)
    return HttpResponse(simplejson.dumps(a), mimetype="application/json")


def multi_molecule(request, string):
    form = JobForm.get_form(request, "{{ name }}")
    add = "" if request.GET.get("view") else "attachment; "

    if form.is_valid():
        d = dict(form.cleaned_data)
        if request.method == "GET":
            molecule = request.REQUEST.get("molname", "")
            d = form.get_single_data(molecule)
            response = HttpResponse(write_job(**d), content_type="text/plain")
            response['Content-Disposition'] = add + 'filename=%s.job' % molecule
            return response

        elif request.method == "POST":
            d["keywords"] = request.REQUEST.get("keywords", None)
            cred = d.pop("credential")
            a = cluster.interface.run_standard_jobs(cred, string, **d)
            return HttpResponse(simplejson.dumps(a), mimetype="application/json")

    keywords = request.REQUEST.get("keywords", "")
    c = Context({
        "pagename": string,
        "form": form,
        "gjf": "checked",
        "encoded_keywords": '?' + urllib.urlencode({"keywords": keywords}) if keywords else '',
        "keywords": keywords,
        })
    return render(request, "chem/multi_molecule.html", c)


def multi_molecule_zip(request, string):
    keywords = request.GET.get("keywords")

    try:
        molecules, warnings, errors = _get_molecule_warnings(string)
    except ValueError:
        c = Context({
            "error": "The operation timed out."
            })
        return render(request, "chem/multi_molecule.html", c)

    if request.GET.get("job"):
        form = JobForm.get_form(request, "{{ name }}")
        if not form.is_valid():
            keywords = request.GET.get("keywords")
            f = lambda x: 'checked' if request.GET.get(x) else ''

            c = Context({
                "molecules": zip(molecules, errors, warnings),
                "pagename": string,
                "form": form,
                "gjf": f("gjf"),
                "mol2": f("mol2"),
                "image": f("image"),
                "job": f("job"),
                "keywords": '?' + urllib.urlencode({"keywords": keywords}) if keywords else '',
                })
            return render(request, "chem/multi_molecule.html", c)
    else:
        form = None

    options = [x for x in ("image", "mol2", "job", "gjf") if request.GET.get(x)]
    ret_zip = get_multi_molecule(molecules, keywords, options, form)

    response = HttpResponse(ret_zip, mimetype="application/zip")
    response["Content-Disposition"] = "attachment; filename=molecules.zip"
    return response


def write_gjf(request, molecule):
    keywords = request.GET.get("keywords")
    add = "" if request.GET.get("view") else "attachment; "

    out = gjfwriter.GJFWriter(molecule, keywords)
    f = StringIO(out.get_gjf())
    response = HttpResponse(FileWrapper(f), content_type="text/plain")
    response['Content-Disposition'] = add + 'filename=%s.gjf' % molecule
    return response


def write_mol2(request, molecule):
    add = "" if request.GET.get("view") else "attachment; "

    out = gjfwriter.GJFWriter(molecule, '')
    f = StringIO(out.get_mol2())
    response = HttpResponse(FileWrapper(f), content_type="text/plain")
    response['Content-Disposition'] = add + 'filename=%s.mol2' % molecule
    return response


def write_png(request, molecule):
    scale = request.GET.get("scale", 10)

    out = gjfwriter.GJFWriter(molecule, '')
    response = HttpResponse(content_type="image/png")
    out.molecule.draw(int(scale)).save(response, "PNG")
    response['Content-Disposition'] = 'filename=%s.png' % molecule
    return response


def report(request, molecule):
    if request.user.is_authenticated():
        email = request.user.email
    else:
        email = ""

    if request.method == "POST":
        report = ErrorReport(molecule=molecule)
        form = ErrorReportForm(request.POST,
            instance=report,
            initial={"email": email})
        if form.is_valid():
            form.save()
            return redirect(molecule_detail, molecule)
    else:
        form = ErrorReportForm(initial={"email": email})

    c = Context({
        "form": form,
        "molecule": molecule
        })
    return render(request, "chem/report.html", c)
