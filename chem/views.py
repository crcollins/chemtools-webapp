import os
import zipfile
import logging
import json

from django.shortcuts import render, redirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.servers.basehttp import FileWrapper
from django.core.serializers.json import DjangoJSONEncoder
from crispy_forms.utils import render_crispy_form

from models import ErrorReport
from forms import ErrorReportForm, JobForm, UploadForm, MoleculeForm
from utils import get_multi_molecule_status, get_molecule_info_status, \
                autoflip_check, get_molecule_status

from chemtools import gjfwriter
from chemtools import fileparser, dataparser
from chemtools.mol_name import name_expansion
from chemtools.interface import get_multi_molecule, get_multi_job
import cluster.interface
from project.utils import StringIO
from data import load_data


logger = logging.getLogger(__name__)


def index(request):
    molecules = [x for x in request.REQUEST.getlist("molecules[]") if x]
    if molecules:
        molecule = ','.join(molecules)
        func = molecule_detail
        if set(",{}$") & set(molecule):
            func = multi_molecule
        autoflip = "?autoflip=true" if request.REQUEST.get("autoflip") else ""
        url = reverse(func, args=(molecule, )) + autoflip
        return HttpResponseRedirect(url)
    return render(request, "chem/index.html")


###########################################################
###########################################################
# Generation Stuff
###########################################################
###########################################################

def multi_job(request):
    form = JobForm.get_form(request, "{{ name }}")

    c = {
        "form": form,
    }
    if not form.is_valid(request.method):
        if request.is_ajax():
            job_form_html = render_crispy_form(
                form, context=RequestContext(request))
            a = {
                "success": False,
                "job_form_html": job_form_html,
                "mol_form_html": '',
            }
            return HttpResponse(json.dumps(a),
                                content_type="application/json")
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
            return HttpResponse(json.dumps(temp),
                                content_type="application/json")
        else:
            return HttpResponse(json.dumps(a),
                                content_type="application/json")

    string = request.REQUEST.get('filenames', '').replace('\r\n', ',').replace('\n', ',')
    ret_zip = get_multi_job(string, form)
    response = HttpResponse(ret_zip, content_type="application/zip")
    response["Content-Disposition"] = "attachment; filename=output.zip"
    return response


def molecule_check(request, string):
    a = {
        "error": None,
    }
    try:
        autoflip = request.REQUEST.get("autoflip")
        molecules, warnings, errors, news = get_multi_molecule_status(
            string, autoflip=autoflip)
        # This is used to fix the issue with ( and ) not being allowed for
        # the id of an HTML tag.
        name_ids = [x.replace('(', 'z').replace(')', 'z') for x in molecules]
        a["molecules"] = zip(molecules, warnings, errors, news, name_ids)
    except ValueError as e:
        logger.warn(str(e))
        a["error"] = str(e)
        a["molecules"] = None
    if request.REQUEST.get("html", ''):
        html = render_to_string("chem/multi_table.html", a)
        return HttpResponse(html)
    else:
        return HttpResponse(json.dumps(a), content_type="application/json")


@autoflip_check
def molecule_detail(request, molecule):
    job_form = JobForm.get_form(request, molecule)
    mol_form = MoleculeForm(request.REQUEST)

    job_is_valid = job_form.is_valid(request.method)
    mol_is_valid = mol_form.is_valid()

    if job_is_valid and mol_is_valid:
        return job_form.get_results(request, molecule, mol_form)
    elif request.is_ajax():
        job_form_html = render_crispy_form(
            job_form, context=RequestContext(request))
        mol_form_html = render_crispy_form(
            mol_form, context=RequestContext(request))
        a = {
            "success": False,
            "job_form_html": job_form_html,
            "mol_form_html": mol_form_html,
        }
        return HttpResponse(json.dumps(a), content_type="application/json")

    a = get_molecule_info_status(molecule)
    a["job_form"] = job_form
    a["mol_form"] = MoleculeForm()
    return render(request, "chem/molecule_detail.html", a)


@autoflip_check
def molecule_detail_json(request, molecule):
    if request.REQUEST.get("geometry"):
        mol, _, _, _ = get_molecule_status(molecule)
        a = mol.get_json()
    else:
        a = get_molecule_info_status(molecule)
    return HttpResponse(json.dumps(a, cls=DjangoJSONEncoder),
                        content_type="application/json")


def multi_molecule(request, string):
    if request.REQUEST.get("random"):
        amount = int(request.REQUEST.get("random"))
        string = ','.join(name_expansion(string, rand=amount))

    job_form = JobForm.get_form(request, "{{ name }}")
    mol_form = MoleculeForm(request.REQUEST)

    job_is_valid = job_form.is_valid(request.method)
    mol_is_valid = mol_form.is_valid()

    if job_is_valid and mol_is_valid:
        return job_form.get_results(request, string, mol_form)
    elif request.is_ajax():
        job_form_html = render_crispy_form(
            job_form, context=RequestContext(request))
        mol_form_html = render_crispy_form(
            mol_form, context=RequestContext(request))
        a = {
            "success": False,
            "job_form_html": job_form_html,
            "mol_form_html": mol_form_html,
        }
        return HttpResponse(json.dumps(a), content_type="application/json")

    c = {
        "pagename": string,
        "job_form": job_form,
        "mol_form": MoleculeForm(),
        "gjf": "checked",
        "autoflip": request.REQUEST.get("autoflip"),
    }
    return render(request, "chem/multi_molecule.html", c)


def multi_molecule_zip(request, string):
    try:
        autoflip = request.REQUEST.get("autoflip")
        molecules, warnings, errors, news = get_multi_molecule_status(
            string, autoflip=autoflip)
    except ValueError as e:
        logger.warn(str(e))
        c = {
            "error": str(e)
        }
        return render(request, "chem/multi_molecule.html", c)

    mol_form = MoleculeForm(request.REQUEST)
    mol_form.is_valid()
    if request.REQUEST.get("job"):
        job_form = JobForm.get_form(request, "{{ name }}")
        if not job_form.is_valid():
            f = lambda x: 'checked' if request.REQUEST.get(x) else ''
            c = {
                "pagename": string,
                "job_form": job_form,
                "mol_form": mol_form,
                "gjf": f("gjf"),
                "mol2": f("mol2"),
                "image": f("image"),
                "job": f("job"),
            }
            return render(request, "chem/multi_molecule.html", c)
    else:
        job_form = None

    selection = ("image", "mol2", "job", "gjf")
    options = [x for x in selection if request.REQUEST.get(x)]
    if request.REQUEST.get("new", ''):
        molecules = [x for i, x in enumerate(molecules) if news[i]]
    ret_zip = get_multi_molecule(molecules, options, mol_form, job_form)

    response = HttpResponse(ret_zip, content_type="application/zip")
    response["Content-Disposition"] = "attachment; filename=molecules.zip"
    return response


@autoflip_check
def write_gjf(request, molecule):
    mol_form = MoleculeForm(request.REQUEST)
    mol_form.is_valid()
    add = "" if request.REQUEST.get("view") else "attachment; "

    mol_settings = dict(mol_form.cleaned_data)
    out = gjfwriter.NamedMolecule(molecule, **mol_settings)
    response = HttpResponse(out.get_gjf(), content_type="text/plain")
    response['Content-Disposition'] = add + 'filename=%s.gjf' % molecule
    return response


@autoflip_check
def write_mol2(request, molecule):
    mol_form = MoleculeForm(request.REQUEST)
    mol_form.is_valid()
    add = "" if request.REQUEST.get("view") else "attachment; "

    mol_settings = dict(mol_form.cleaned_data)
    out = gjfwriter.NamedMolecule(molecule, **mol_settings)
    response = HttpResponse(out.get_mol2(), content_type="text/plain")
    response['Content-Disposition'] = add + 'filename=%s.mol2' % molecule
    return response


@autoflip_check
def write_png(request, molecule):
    mol_form = MoleculeForm(request.REQUEST)
    mol_form.is_valid()
    mol_settings = dict(mol_form.cleaned_data)

    out = gjfwriter.NamedMolecule(molecule, **mol_settings)
    response = HttpResponse(out.get_png(), content_type="image/png")
    response['Content-Disposition'] = 'filename=%s.png' % molecule
    return response


@autoflip_check
def write_svg(request, molecule):
    mol_form = MoleculeForm(request.REQUEST)
    mol_form.is_valid()
    mol_settings = dict(mol_form.cleaned_data)

    out = gjfwriter.NamedMolecule(molecule, **mol_settings)
    response = HttpResponse(
        out.get_svg(), content_type="image/svg+xml")
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
        "structureview": view_structure,
    }

    if request.method == "POST":
        upload_form = UploadForm(request.POST or None, files=request.FILES)
        if upload_form.is_valid():
            return switch[request.POST["options"]](request, upload_form)
    else:
        upload_form = UploadForm()
    c = {
        "upload_form": upload_form,
        "job_form": JobForm.get_form(request, "{{ name }}", initial=True),
    }
    return render(request, "chem/upload_log.html", c)


def parse_log(request, upload_form):
    parser = fileparser.LogSet()
    for f in upload_form.cleaned_data["files"]:
        parser.parse_file(f)

    output = parser.format_output()
    f2 = StringIO(output)

    if upload_form.cleaned_data['store'] and request.user.is_staff:
        number_added = load_data.main(f2)
        logger.info("%d datapoint(s) added to database" % number_added)
        output += "\n\n\n%d datapoint(s) added to database." % number_added

    response = HttpResponse(output, content_type="text/plain")
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

    response = HttpResponse(ret_zip, content_type="application/zip")
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
            logger.warn("There was an error when trying to reset a gjf: '%s'" % str(e))
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
                return HttpResponse(json.dumps(a),
                                    content_type="application/json")
            c = {
                "job_form": job_form,
                "upload_form": upload_form,
            }
            return render(request, "chem/upload_log.html", c)

        d = dict(job_form.cleaned_data)
        cred = d.pop("credential")
        a = cluster.interface.run_jobs(cred, names, strings, **d)
        a["failed"].extend(errors)
        do_html = request.REQUEST.get("html", False)
        if do_html:
            html = render_to_string("chem/multi_submit.html", a)
            temp = {"success": True, "html": html}
            return HttpResponse(json.dumps(temp),
                                content_type="application/json")
        else:
            return HttpResponse(json.dumps(a),
                                content_type="application/json")

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

    response = HttpResponse(ret_zip, content_type="application/zip")
    response["Content-Disposition"] = "attachment; filename=output.zip"
    return response


def view_structure(request, upload_form):
    scale = request.REQUEST.get("scale", 10)

    images = []
    errors = []
    for f in upload_form.cleaned_data["files"]:
        out = gjfwriter.Molecule(f.name)
        try:
            out.from_gjf(f)
        except AssertionError:
            try:
                out.from_log(f)
            except Exception:
                errors.append("%s is an invalid file" % f.name)
                continue
        images.append(out.get_png_data_url(scale=scale))

    c = {
        "errors": errors,
        "images": images,
    }
    return render(request, "chem/structure_view.html", c)

###########################################################
###########################################################
# Other
###########################################################
###########################################################


@autoflip_check
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
            logger.info("'%s' was reported as having an error by %s." % (molecule, email))
            return redirect(molecule_detail, molecule)
    else:
        form = ErrorReportForm(initial={"email": email})

    c = {
        "form": form,
        "molecule": molecule
    }
    return render(request, "chem/report.html", c)
