from cStringIO import StringIO
import zipfile
import os
import urllib
import re
import time

from django.shortcuts import render, redirect
from django.template import Context
from django.http import HttpResponse, HttpResponseRedirect
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.utils import simplejson

from models import ErrorReport, ErrorReportForm, JobForm

from chemtools import gjfwriter
from chemtools.utils import name_expansion, write_job
import cluster.utils

def index(request):
    if request.GET.get("molecule"):

        func = gen_detail
        if set(",{}$") & set(request.GET.get("molecule")):
            func = gen_multi_detail

        a = {"keywords": request.GET.get("keywords")}
        if a["keywords"] != "B3LYP/6-31g(d)":
            b = "%s?%s" % (reverse(func, args=(request.GET.get("molecule"), )),
                urllib.urlencode(a))
            return HttpResponseRedirect(b)
        else:
            return redirect(func, request.GET.get("molecule"))
    return render(request, "chem/index.html")


###########################################################
###########################################################
# Generation Stuff
###########################################################
###########################################################

def _get_molecules_info(string):
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

def multi_job(request):
    form = JobForm.get_form(request, "{{ name }}")

    if not form.is_valid():
        c = Context({
            "form": form,
            })
        return render(request, "chem/multi_job.html", c)

    buff = StringIO()
    zfile = zipfile.ZipFile(buff, 'w', zipfile.ZIP_DEFLATED)
    d = dict(form.cleaned_data)

    string = request.REQUEST.get('filenames', '').replace('\n', ',')
    for name in name_expansion(string):
        if not name:
            continue
        dnew = d.copy()
        name, _ = os.path.splitext(name)
        dnew["name"] = re.sub(r"{{\s*name\s*}}", name, dnew["name"])
        zfile.writestr("%s.%sjob" % (name, dnew.get("cluster")), write_job(**dnew))

    zfile.close()
    buff.flush()

    ret_zip = buff.getvalue()
    buff.close()

    response = HttpResponse(ret_zip, mimetype="application/zip")
    response["Content-Disposition"] = "attachment; filename=output.zip"
    return response

def molecule_check(request, string):
    a = {
        "error": None,
        "molecules": [[x] for x in name_expansion(string)]
    }
    try:
        molecules, warnings, errors = _get_molecules_info(string)
        a["molecules"] = zip(molecules, warnings, errors)
    except ValueError:
        a["error"] = "The operation timed out."
        a["molecules"] = None
    return HttpResponse(simplejson.dumps(a), mimetype="application/json")

def gen_detail(request, molecule):
    _, warnings, errors = _get_molecules_info(molecule)
    form = JobForm.get_form(request, molecule)
    keywords = request.REQUEST.get("keywords")
    add = "" if request.GET.get("view") else "attachment; "

    if form.is_valid():
        d = dict(form.cleaned_data)
        if request.method == "GET":
            response = HttpResponse(write_job(**d), content_type="text/plain")
            response['Content-Disposition'] = add + 'filename=%s.job' % molecule
            return response
        elif request.method == "POST":
            d["keywords"] = keywords
            a = cluster.utils.run_standard_job(request.user, molecule, **d)
            return HttpResponse(simplejson.dumps(a), mimetype="application/json")

    if not errors[0]:
        exactname = gjfwriter.get_exact_name(molecule)
    else:
        exactname = ''

    c = Context({
        "molecule": molecule,
        "exact_name": exactname,
        "form": form,
        "known_errors": warnings[0],
        "error_message": errors[0],
        "encoded_keywords": '?' + urllib.urlencode({"keywords": keywords}) if keywords else '',
        "keywords": keywords,
        })
    return render(request, "chem/molecule_detail.html", c)

def gen_multi_detail(request, string):
    form = JobForm.get_form(request, "{{ name }}")
    keywords = request.REQUEST.get("keywords", "")
    add = "" if request.GET.get("view") else "attachment; "

    if form.is_valid():
        d = dict(form.cleaned_data)
        if request.method == "GET":
            molecule = request.REQUEST.get("molname","")
            d["name"] = re.sub(r"{{\s*name\s*}}", molecule, d["name"])
            response = HttpResponse(write_job(**d), content_type="text/plain")
            response['Content-Disposition'] = add + 'filename=%s.job' % molecule
            return response

        elif request.method == "POST":
            d["keywords"] = keywords
            a = cluster.utils.run_standard_jobs(request.user, string, **d)
            return HttpResponse(simplejson.dumps(a), mimetype="application/json")

    c = Context({
        "pagename": string,
        "form": form,
        "gjf": "checked",
        "encoded_keywords": '?' + urllib.urlencode({"keywords": keywords}) if keywords else '',
        "keywords": keywords,
        })
    return render(request, "chem/multi_molecule.html", c)

def gen_multi_detail_zip(request, string):
    keywords = request.GET.get("keywords")

    buff = StringIO()
    zfile = zipfile.ZipFile(buff, "w", zipfile.ZIP_DEFLATED)

    try:
        molecules, warnings, errors = _get_molecules_info(string)
    except ValueError:
        c = Context({
            "error": "The operation timed out."
            })
        return render(request, "chem/multi_molecule.html", c)

    if request.GET.get("job"):
        form = JobForm.get_form(request, "{{ name }}")
        if form.is_valid():
            d = dict(form.cleaned_data)
        else:
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

    generrors = []
    for name in molecules:
        try:
            out = gjfwriter.GJFWriter(name, keywords)
            others = False

            if request.GET.get("image"):
                zfile.writestr(out.name + ".png", out.get_png(10))
                others = True
            if request.GET.get("mol2"):
                zfile.writestr(name + ".mol2", out.get_mol2())
                others = True
            if request.GET.get("job"):
                dnew = d.copy()
                dnew["name"] = re.sub(r"{{\s*name\s*}}", name, dnew["name"])
                zfile.writestr(name + ".job", write_job(**dnew))
                others = True

            if request.GET.get("gjf") or not others:
                zfile.writestr(name + ".gjf", out.get_gjf())

        except Exception as e:
            generrors.append("%s - %s" % (name,  e))
    if generrors:
        zfile.writestr("errors.txt", '\n'.join(generrors))

    zfile.close()
    buff.flush()

    ret_zip = buff.getvalue()
    buff.close()

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
            return redirect(gen_detail, molecule)
    else:
        form = ErrorReportForm(initial={"email" : email})

    c = Context({
        "form": form,
        "molecule": molecule
        })
    return render(request, "chem/report.html", c)