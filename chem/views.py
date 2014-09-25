import os
import urllib
import zipfile

from django.shortcuts import render, redirect
from django.template import Context, RequestContext
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson
from crispy_forms.utils import render_crispy_form

from models import ErrorReport
from forms import ErrorReportForm, JobForm, UploadForm, MoleculeForm
from utils import get_multi_molecule_warnings, get_molecule_info
from utils import parse_file_list, find_sets, convert_logs

from chemtools import gjfwriter
from chemtools import fileparser, dataparser
from chemtools.interface import get_multi_molecule, get_multi_job
import cluster.interface
from project.utils import StringIO


def index(request):
    molecule = request.REQUEST.get("molecule")
    if molecule:
        func = molecule_detail
        if set(",{}$") & set(molecule):
            func = multi_molecule
        return redirect(func, molecule)
    return render(request, "chem/index.html")


###########################################################
###########################################################
# Generation Stuff
###########################################################
###########################################################

def multi_job(request):
    form = JobForm.get_form(request, "{{ name }}")

    c = Context({
        "form": form,
        })
    if not form.is_valid(request.method):
        if request.is_ajax():
            job_form_html = render_crispy_form(form, context=RequestContext(request))
            a = {
                "success": False,
                "job_form_html": job_form_html,
                "mol_form_html": '',
            }
            return HttpResponse(simplejson.dumps(a),
                                mimetype="application/json")
        return render(request, "chem/multi_job.html", c)

    d = dict(form.cleaned_data)
    if request.method == "POST":
        cred = d.pop("credential")
        files = request.FILES.getlist("files")
        strings = [''.join(f.readlines()) for f in files]
        names = [os.path.splitext(f.name)[0] for f in files]
        a = cluster.interface.run_jobs(cred, names, strings, **d)
        do_html = request.REQUEST.get("html", False)
        if do_html:
            html = render_to_string("chem/multi_submit.html", a)
            temp = {"success": True, "html": html}
            return HttpResponse(simplejson.dumps(temp),
                                mimetype="application/json")
        else:
            return HttpResponse(simplejson.dumps(a),
                                mimetype="application/json")

    string = request.REQUEST.get('filenames', '').replace('\n', ',')
    ret_zip = get_multi_job(string, form)
    response = HttpResponse(ret_zip, mimetype="application/zip")
    response["Content-Disposition"] = "attachment; filename=output.zip"
    return response


def molecule_check(request, string):
    a = {
        "error": None,
    }
    try:
        molecules, warnings, errors, news = get_multi_molecule_warnings(
                                                                        string)
        a["molecules"] = zip(molecules, warnings, errors, news)
    except ValueError as e:
        a["error"] = str(e)
        a["molecules"] = None
    if request.REQUEST.get("html", ''):
        html = render_to_string("chem/multi_table.html", a)
        return HttpResponse(html)
    else:
        return HttpResponse(simplejson.dumps(a), mimetype="application/json")


def molecule_detail(request, molecule):
    job_form = JobForm.get_form(request, molecule)
    mol_form = MoleculeForm(request.REQUEST)

    job_is_valid = job_form.is_valid(request.method)
    mol_is_valid = mol_form.is_valid()

    if job_is_valid and mol_is_valid:
        return job_form.get_results(request, molecule, mol_form)
    elif request.is_ajax():
        job_form_html = render_crispy_form(job_form, context=RequestContext(request))
        mol_form_html = render_crispy_form(mol_form, context=RequestContext(request))
        a = {
            "success": False,
            "job_form_html": job_form_html,
            "mol_form_html": mol_form_html,
        }
        return HttpResponse(simplejson.dumps(a), mimetype="application/json")

    a = get_molecule_info(molecule)
    a["job_form"] = job_form
    a["mol_form"] = MoleculeForm()
    c = Context(a)
    return render(request, "chem/molecule_detail.html", c)


def molecule_detail_json(request, molecule):
    a = get_molecule_info(molecule)
    return HttpResponse(simplejson.dumps(a, cls=DjangoJSONEncoder),
                    mimetype="application/json")


def multi_molecule(request, string):
    job_form = JobForm.get_form(request, "{{ name }}")
    mol_form = MoleculeForm(request.REQUEST)

    job_is_valid = job_form.is_valid(request.method)
    mol_is_valid = mol_form.is_valid()

    if job_is_valid and mol_is_valid:
        return job_form.get_results(request, string, mol_form)
    elif request.is_ajax():
        job_form_html = render_crispy_form(job_form, context=RequestContext(request))
        mol_form_html = render_crispy_form(mol_form, context=RequestContext(request))
        a = {
            "success": False,
            "job_form_html": job_form_html,
            "mol_form_html": mol_form_html,
        }
        return HttpResponse(simplejson.dumps(a), mimetype="application/json")

    c = Context({
        "pagename": string,
        "job_form": job_form,
        "mol_form": MoleculeForm(),
        "gjf": "checked",
        })
    return render(request, "chem/multi_molecule.html", c)


def multi_molecule_zip(request, string):
    try:
        molecules, warnings, errors, news = get_multi_molecule_warnings(
                                                                        string)
    except ValueError as e:
        c = Context({
            "error": str(e)
            })
        return render(request, "chem/multi_molecule.html", c)

    mol_form = MoleculeForm(request.REQUEST)
    mol_form.is_valid()
    if request.REQUEST.get("job"):
        job_form = JobForm.get_form(request, "{{ name }}")
        if not job_form.is_valid():
            f = lambda x: 'checked' if request.REQUEST.get(x) else ''
            c = Context({
                "pagename": string,
                "job_form": job_form,
                "mol_form": mol_form,
                "gjf": f("gjf"),
                "mol2": f("mol2"),
                "image": f("image"),
                "job": f("job"),
                })
            return render(request, "chem/multi_molecule.html", c)
    else:
        job_form = None

    selection = ("image", "mol2", "job", "gjf")
    options = [x for x in selection if request.REQUEST.get(x)]
    if request.REQUEST.get("new", ''):
        molecules = [x for i, x in enumerate(molecules) if news[i]]
    ret_zip = get_multi_molecule(molecules, options, mol_form, job_form)

    response = HttpResponse(ret_zip, mimetype="application/zip")
    response["Content-Disposition"] = "attachment; filename=molecules.zip"
    return response


def write_gjf(request, molecule):
    mol_form = MoleculeForm(request.REQUEST)
    mol_form.is_valid()
    add = "" if request.REQUEST.get("view") else "attachment; "

    mol_settings = dict(mol_form.cleaned_data)
    out = gjfwriter.Benzobisazole(molecule, **mol_settings)
    f = StringIO(out.get_gjf())
    response = HttpResponse(FileWrapper(f), content_type="text/plain")
    response['Content-Disposition'] = add + 'filename=%s.gjf' % molecule
    return response


def write_mol2(request, molecule):
    mol_form = MoleculeForm(request.REQUEST)
    mol_form.is_valid()
    add = "" if request.REQUEST.get("view") else "attachment; "

    mol_settings = dict(mol_form.cleaned_data)
    out = gjfwriter.Benzobisazole(molecule, **mol_settings)
    f = StringIO(out.get_mol2())
    response = HttpResponse(FileWrapper(f), content_type="text/plain")
    response['Content-Disposition'] = add + 'filename=%s.mol2' % molecule
    return response


def write_png(request, molecule):
    scale = request.REQUEST.get("scale", 10)

    out = gjfwriter.Benzobisazole(molecule)
    response = HttpResponse(out.get_png(int(scale)), content_type="image/png")
    response['Content-Disposition'] = 'filename=%s.png' % molecule
    return response


def write_svg(request, molecule):
    scale = request.REQUEST.get("scale", 10)

    out = gjfwriter.Benzobisazole(molecule)
    response = HttpResponse(out.get_svg(int(scale)), content_type="image/svg+xml")
    response['Content-Disposition'] = 'filename=%s.svg' % molecule
    return response

###########################################################
###########################################################
# Upload
###########################################################
###########################################################

def upload_data(request):
    switch = {
        "logparse": parse_log,
        "longchain": long_chain_limit,
        "gjfreset": reset_gjf,
        "gjfview": view_gjf,
    }

    if request.method == "POST":
        upload_form = UploadForm(request.POST or None, files=request.FILES)
        if upload_form.is_valid():
            return switch[request.POST["options"]](request, upload_form)
    else:
        upload_form = UploadForm()
    c = Context({
        "upload_form": upload_form,
        "job_form": JobForm.get_form(request, "{{ name }}", initial=True),
        })
    return render(request, "chem/upload_log.html", c)


def parse_log(request, upload_form):
    parser = fileparser.LogSet()
    for f in upload_form.cleaned_data["files"]:
        parser.parse_file(f)

    f = StringIO(parser.format_output())
    response = HttpResponse(FileWrapper(f), content_type="text/plain")
    return response


def long_chain_limit(request, upload_form):
    buff = StringIO()
    zfile = zipfile.ZipFile(buff, 'w', zipfile.ZIP_DEFLATED)
    for f in upload_form.cleaned_data["files"]:
        parser = dataparser.DataParser(f)
        homolumo, gap = parser.get_graphs()

        name, _ = os.path.splitext(f.name)
        if len(upload_form.cleaned_data["files"]) > 1:
            zfile.writestr(name + "/output.txt", parser.format_output())
            zfile.writestr(name + "/homolumo.eps", homolumo.getvalue())
            zfile.writestr(name + "/gap.eps", gap.getvalue())
        else:
            zfile.writestr("output.txt", parser.format_output())
            zfile.writestr("homolumo.eps", homolumo.getvalue())
            zfile.writestr("gap.eps", gap.getvalue())

    if len(upload_form.cleaned_data["files"]) > 1:
        name = "output"
    zfile.close()
    buff.flush()

    ret_zip = buff.getvalue()
    buff.close()

    response = HttpResponse(ret_zip, mimetype="application/zip")
    response["Content-Disposition"] = "attachment; filename=%s.zip" % name
    return response


def reset_gjf(request, upload_form):
    job_form = JobForm.get_form(request, "{{ name }}")

    errors = []
    strings = []
    names = []
    for f in upload_form.cleaned_data["files"]:
        try:
            parser = fileparser.Log(f)

            name, _ = os.path.splitext(f.name)
            td = False
            if request.REQUEST.get("td_reset"):
                name += '_TD'
                td = True
            strings.append(parser.format_gjf(td=td))
            names.append(name)
        except Exception as e:
            errors.append((f.name, e))

    if request.REQUEST.get("gjf_submit"):
        if not job_form.is_valid(request.method):
            if request.is_ajax():
                upload_form_html = render_crispy_form(upload_form,
                                            context=RequestContext(request))
                job_form_html = render_crispy_form(job_form,
                                            context=RequestContext(request))
                a = {
                    "success": False,
                    "job_form_html": job_form_html,
                    "upload_form_html": upload_form_html,
                }
                return HttpResponse(simplejson.dumps(a),
                                    mimetype="application/json")
            c = Context({
                "job_form": job_form,
                "upload_form": upload_form,
                })
            return render(request, "chem/upload_log.html", c)

        d = dict(job_form.cleaned_data)
        cred = d.pop("credential")
        a = cluster.interface.run_jobs(cred, names, strings, **d)
        a["failed"].extend(errors)
        do_html = request.REQUEST.get("html", False)
        if do_html:
            html = render_to_string("chem/multi_submit.html", a)
            temp = {"success": True, "html": html}
            return HttpResponse(simplejson.dumps(temp),
                                mimetype="application/json")
        else:
            return HttpResponse(simplejson.dumps(a),
                                mimetype="application/json")

    buff = StringIO()
    zfile = zipfile.ZipFile(buff, 'w', zipfile.ZIP_DEFLATED)
    for name, string in zip(names, strings):
        zfile.writestr("%s.gjf" % name, string)
    if errors:
        temp = ['%s - %s' % (name, error) for (name, error) in errors]
        zfile.writestr("errors.txt", '\n'.join(temp))
    zfile.close()
    buff.flush()
    ret_zip = buff.getvalue()
    buff.close()

    response = HttpResponse(ret_zip, mimetype="application/zip")
    response["Content-Disposition"] = "attachment; filename=output.zip"
    return response


def view_gjf(request, upload_form):
    scale = request.REQUEST.get("scale", 10)

    images = []
    for f in upload_form.cleaned_data["files"]:
        out = gjfwriter.Molecule(f.name)
        out.from_gjf(f)
        images.append(out.get_png_data_url())

    c = Context({
        "images": images,
        })
    return render(request, "chem/gjf_view.html", c)

###########################################################
###########################################################
# Other
###########################################################
###########################################################

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
