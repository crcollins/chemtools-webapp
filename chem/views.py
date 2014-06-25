from cStringIO import StringIO
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
from forms import ErrorReportForm, JobForm, UploadForm
from utils import get_multi_molecule_warnings, get_molecule_info
from utils import parse_file_list, find_sets, convert_logs

from chemtools import gjfwriter
from chemtools import fileparser, dataparser
from chemtools.constants import KEYWORDS
from chemtools.interface import get_multi_molecule, get_multi_job
import cluster.interface
from data.models import JobTemplate
from project.utils import StringIO


def index(request):
    if request.REQUEST.get("molecule"):

        func = molecule_detail
        if set(",{}$") & set(request.REQUEST.get("molecule")):
            func = multi_molecule

        params = {"keywords": request.REQUEST.get("keywords", None)}
        if params["keywords"] != KEYWORDS:
            url = "%s?%s" % (reverse(func,
                                    args=(request.REQUEST.get("molecule"), )),
                urllib.urlencode(params))
            return HttpResponseRedirect(url)
        else:
            return redirect(func, request.REQUEST.get("molecule"))
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
            form_html = render_crispy_form(form,
                                        context=RequestContext(request))
            a = {"success": False, "form_html": form_html}
            return HttpResponse(simplejson.dumps(a),
                                mimetype="application/json")
        return render(request, "chem/multi_job.html", c)

    d = dict(form.cleaned_data)
    if request.method == "POST":
        cred = d.pop("credential")
        d["keywords"] = request.REQUEST.get("keywords", None)
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
        molecules, warnings, errors, uniques = get_multi_molecule_warnings(
                                                                        string)
        a["molecules"] = zip(molecules, warnings, errors, uniques)
    except ValueError as e:
        a["error"] = str(e)
        a["molecules"] = None
    if request.REQUEST.get("html", ''):

        html = render_to_string("chem/multi_table.html", a)
        return HttpResponse(html)
    else:
        return HttpResponse(simplejson.dumps(a), mimetype="application/json")


def molecule_detail(request, molecule):
    form = JobForm.get_form(request, molecule)
    keywords = request.REQUEST.get("keywords", '')

    if form.is_valid(request.method):
        return form.get_results(request, molecule)
    elif request.is_ajax():
        form_html = render_crispy_form(form, context=RequestContext(request))
        a = {"success": False, "form_html": form_html}
        return HttpResponse(simplejson.dumps(a), mimetype="application/json")

    keywords2 = request.REQUEST.get("keywords", KEYWORDS)
    a = get_molecule_info(molecule, keywords2)
    a["form"] = form
    c = Context(a)
    return render(request, "chem/molecule_detail.html", c)


def molecule_detail_json(request, molecule):
    keywords = request.REQUEST.get("keywords", KEYWORDS)
    a = get_molecule_info(molecule, keywords)
    return HttpResponse(simplejson.dumps(a, cls=DjangoJSONEncoder),
                    mimetype="application/json")


def multi_molecule(request, string):
    form = JobForm.get_form(request, "{{ name }}")

    if form.is_valid(request.method):
        return form.get_results(request, string)
    elif request.is_ajax():
        form_html = render_crispy_form(form, context=RequestContext(request))
        a = {"success": False, "form_html": form_html}
        return HttpResponse(simplejson.dumps(a), mimetype="application/json")

    keywords = request.REQUEST.get("keywords", "")
    encoded_keywords = '?' + urllib.urlencode({"keywords": keywords})
    encoded_zip = '?' + urllib.urlencode({"keywords": keywords})
    c = Context({
        "pagename": string,
        "form": form,
        "gjf": "checked",
        "encoded_keywords": encoded_keywords if keywords else '',
        "keywords": keywords,
        "encoded_zip": encoded_zip,
        })
    return render(request, "chem/multi_molecule.html", c)


def multi_molecule_zip(request, string):
    keywords = request.REQUEST.get("keywords")
    unique = request.REQUEST.get("unique", '')

    try:
        molecules, warnings, errors, uniques = get_multi_molecule_warnings(
                                                                        string)
    except ValueError as e:
        c = Context({
            "error": str(e)
            })
        return render(request, "chem/multi_molecule.html", c)

    if request.REQUEST.get("job"):
        form = JobForm.get_form(request, "{{ name }}")
        if not form.is_valid():
            keywords = request.REQUEST.get("keywords")
            f = lambda x: 'checked' if request.REQUEST.get(x) else ''

            encoded_keywords = '?' + urllib.urlencode({"keywords": keywords})
            c = Context({
                "molecules": zip(molecules, errors, warnings, uniques),
                "pagename": string,
                "form": form,
                "gjf": f("gjf"),
                "mol2": f("mol2"),
                "image": f("image"),
                "job": f("job"),
                "encoded_keywords": encoded_keywords if keywords else '',
                })
            return render(request, "chem/multi_molecule.html", c)
    else:
        form = None

    selection = ("image", "mol2", "job", "gjf")
    options = [x for x in selection if request.REQUEST.get(x)]
    if unique:
        molecules = [x for i, x in enumerate(molecules) if uniques[i]]
    ret_zip = get_multi_molecule(molecules, keywords, options, form)

    response = HttpResponse(ret_zip, mimetype="application/zip")
    response["Content-Disposition"] = "attachment; filename=molecules.zip"
    return response


def write_gjf(request, molecule):
    keywords = request.REQUEST.get("keywords")
    add = "" if request.REQUEST.get("view") else "attachment; "

    out = gjfwriter.Benzobisazole(molecule, keywords=keywords)
    f = StringIO(out.get_gjf())
    response = HttpResponse(FileWrapper(f), content_type="text/plain")
    response['Content-Disposition'] = add + 'filename=%s.gjf' % molecule
    return response


def write_mol2(request, molecule):
    add = "" if request.REQUEST.get("view") else "attachment; "

    out = gjfwriter.Benzobisazole(molecule)
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
        "dataparse": parse_data,
        "gjfreset": reset_gjf,
    }

    if request.method == "POST":
        upload_form = UploadForm(request.POST or None, files=request.FILES)
        if upload_form.is_valid():
            return switch[request.POST["options"]](request)
    else:
        upload_form = UploadForm()
    c = Context({
        "upload_form": upload_form,
        "job_form": JobForm.get_form(request, "{{ name }}", initial=True),
        })
    return render(request, "chem/upload_log.html", c)


def parse_log(request):
    parser = fileparser.LogSet()
    for f in parse_file_list(request.FILES.getlist('files')):
        parser.parse_file(f)

    f = StringIO(parser.format_output())
    response = HttpResponse(FileWrapper(f), content_type="text/plain")
    return response


def parse_data(request):
    files = list(parse_file_list(request.FILES.getlist('files')))
    logsets, files = find_sets(files)

    files.extend(convert_logs(logsets))

    num = len(files)
    if not num:
        raise ValueError("There are no data files to parse.")

    buff = StringIO()
    zfile = zipfile.ZipFile(buff, 'w', zipfile.ZIP_DEFLATED)
    for f in files:
        parser = dataparser.DataParser(f)
        homolumo, gap = parser.get_graphs()

        name, _ = os.path.splitext(f.name)
        if num > 1:
            zfile.writestr(name + "/output.txt", parser.format_output())
            zfile.writestr(name + "/homolumo.eps", homolumo.getvalue())
            zfile.writestr(name + "/gap.eps", gap.getvalue())
        else:
            zfile.writestr("output.txt", parser.format_output())
            zfile.writestr("homolumo.eps", homolumo.getvalue())
            zfile.writestr("gap.eps", gap.getvalue())

    if num > 1:
        name = "output"
    zfile.close()
    buff.flush()

    ret_zip = buff.getvalue()
    buff.close()

    response = HttpResponse(ret_zip, mimetype="application/zip")
    response["Content-Disposition"] = "attachment; filename=%s.zip" % name
    return response


def reset_gjf(request):
    job_form = JobForm.get_form(request, "{{ name }}")
    upload_form = UploadForm(request.POST, files=request.FILES)

    # this should be fine because it already passed the first layer
    upload_form.is_valid()

    errors = []
    strings = []
    names = []
    for f in parse_file_list(request.FILES.getlist('files')):
        parser = fileparser.Log(f)

        name, _ = os.path.splitext(f.name)
        td = False
        if request.REQUEST.get("td_reset"):
            name += '_TD'
            td = True
        try:
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
        d["keywords"] = request.REQUEST.get("keywords", None)
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
