from cStringIO import StringIO
import zipfile
import os

from django.shortcuts import render, redirect
from django.template import Context, RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.core.servers.basehttp import FileWrapper

import gjfwriter
import fileparser
from models import ErrorReport, ErrorReportForm, JobForm, LogForm


def index(request):
    if request.GET.get("molecule"):
        return redirect(gen_detail, request.GET.get("molecule"))
    return render(request, "chem/index.html")

def frag_index(request):
    data = (
        ["Cores" , ("CON", "TON", "TSN", "CSN", "TNN", "CNN", "CCC", "TCC")],
        ["X Groups" , (["A", "H"], ["B", "Cl"], ["C", "Br"], ["D"," CN"], ["E"," CCH"],
            ["F", "OH"], ["G", "SH"], ["H", "NH_2"], ["I", "CH_3"], ["J", "phenyl"], ["K", "TMS"],
             ["L", "OCH_3"])],
        ["Aryl Groups" , (["2", "double"], ["3", "triple"], ["4", "--"], ["5", "--"],
            ["6", "--"], ["7", "--"], ["8", "TZ"], ["9", "EDOT"])],
        ["R Groups" , (["a", "H"], ["b", "Cl"], ["c", "Br"], ["d"," CN"], ["e"," CCH"],
            ["f", "OH"], ["g", "SH"], ["h", "NH_2"], ["i", "CH_3"], ["j", "phenyl"], ["k", "TMS"],
             ["l", "OCH_3"])],
    )
    c = Context({"usable_parts": data})
    return render(request, "chem/frag_index.html", c)

def gen_detail(request, molecule):
    try:
        gjfwriter.parse_name(molecule)
        e = None
    except Exception as e:
        pass
    c = Context({
        "molecule": molecule,
        "known_errors": ErrorReport.objects.filter(molecule=molecule),
        "error_message": e,
        })
    return render(request, "chem/detail.html", c)


def gen_multi_detail(request, molecules):
    if request.GET.get("basis"):
        basis = request.GET.get("basis")
    else:
        basis = ''

    buff = StringIO()
    zfile = zipfile.ZipFile(buff, "w", zipfile.ZIP_DEFLATED)
    errors = ''
    for name in molecules.split(','):
        try:
            out = gjfwriter.Output(name, basis)
            if request.GET.get("image"):
                f = StringIO()
                out.molecule.draw(10).save(f, "PNG")
                zfile.writestr(out.name+".png", f.getvalue())

            if request.GET.get("gjf") is None or request.GET.get("gjf").lower() != "false":
                zfile.writestr(name+".gjf", out.write_file())
        except Exception as e:
            errors += "%s - %s\n" % (name,  e)
    if errors:
        zfile.writestr("errors.txt", errors)

    zfile.close()
    buff.flush()

    ret_zip = buff.getvalue()
    buff.close()

    response = HttpResponse(ret_zip, mimetype="application/zip")
    response["Content-Disposition"] = "attachment; filename=molecules.zip"
    return response


def write_gjf(request, molecule):
    filename = molecule + ".gjf"

    if request.GET.get("basis"):
        basis = request.GET.get("basis")
    else:
        basis = ''

    out = gjfwriter.Output(molecule, basis)
    f = StringIO(out.write_file())
    response = HttpResponse(FileWrapper(f), content_type="text/plain")
    response['Content-Disposition'] = 'filename=%s.gjf' % molecule
    return response

def write_mol2(request, molecule):
    filename = molecule + ".mol2"

    out = gjfwriter.Output(molecule, '')
    f = StringIO(out.write_file(False))
    response = HttpResponse(FileWrapper(f), content_type="text/plain")
    response['Content-Disposition'] = 'filename=%s.mol2' % molecule
    return response

def write_png(request, molecule):
    filename = molecule + ".png"

    if request.GET.get("scale"):
        scale = request.GET.get("scale")
    else:
        scale = 10

    out = gjfwriter.Output(molecule, '')
    response = HttpResponse(content_type="image/png")
    out.molecule.draw(int(scale)).save(response, "PNG")
    response['Content-Disposition'] = 'filename=%s.png' % molecule
    return response

def get_frag(request, frag):
    f = open("chem/data/"+frag, "r")
    response = HttpResponse(FileWrapper(f), content_type="text/plain")
    return response

def get_job(request, molecule):
    a = {}
    for x in ("name", "email", "nodes", "ncpus", "time"):
        if request.GET.get(x):
            a[x] = request.GET[x]

    if a:
        form = JobForm(request.GET, initial=a)
        if form.is_valid():
            c = Context({
                "name" : request.GET["name"],
                "email": request.GET["email"],
                "nodes": request.GET["nodes"],
                "ncpus": int(request.GET["nodes"]) * 16,
                "time" : "%s:00:00" % request.GET["time"],
                "form" : form,
                "molecule": molecule,
                })
            template = "chem/jobs/%sjob.txt" % request.GET["cluster"]
            return render(request, template, c, content_type="text/plain")
    else:
        form = JobForm(initial={"name": molecule})

    c = Context({
        "form": form,
        "molecule": molecule,
        })
    return render(request, "chem/job.html", c)

def report(request, molecule):
    if request.method == "POST":
        report = ErrorReport(molecule=molecule)
        form = ErrorReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/%s' % (molecule, ))
    else:
        form = ErrorReportForm()

    c = Context({
        "form": form,
        "molecule": molecule
        })
    return render(request, "chem/report.html", c)

def upload_data(request):
    if request.method == "POST":
        if request.POST["option"] == "logparse":
            return parse_log(request)
        elif request.POST["option"] == "dataparse":
            return parse_data(request)
        elif request.POST["option"] == "gjfreset":
            return reset_gjf(request)
    form = LogForm()
    c = Context({
        "form": form,
        })
    return render(request, "chem/upload_log.html", c)

def parse_log(request):
    parser = fileparser.LogParser()
    for f in request.FILES.getlist('myfiles'):
        if f.name.endswith(".zip"):
            with zipfile.ZipFile(f, "r") as zfile:
                for name in zfile.namelist():
                    parser.parse_file(zfile.open(name))
        else:
            parser.parse_file(f)
    f = StringIO(parser.format_output())
    response = HttpResponse(FileWrapper(f), content_type="text/plain")
    return response

def parse_data(request):
    buff = StringIO()
    zfile = zipfile.ZipFile(buff, 'w', zipfile.ZIP_DEFLATED)

    for f in request.FILES.getlist('myfiles'):
        parser = fileparser.DataParser(f)
        homolumo, gap = parser.get_graphs()

        name, _ = os.path.splitext(f.name)
        if len(request.FILES.getlist('myfiles')) != 1:
            zfile.writestr(name+"/output.txt", parser.format_output())
            zfile.writestr(name+"/homolumo.eps", homolumo.getvalue())
            zfile.writestr(name+"/gap.eps", gap.getvalue())
        else:
            zfile.writestr("output.txt", parser.format_output())
            zfile.writestr("homolumo.eps", homolumo.getvalue())
            zfile.writestr("gap.eps", gap.getvalue())

    if len(request.FILES.getlist('myfiles')) != 1:
        name = "output"
    zfile.close()
    buff.flush()

    ret_zip = buff.getvalue()
    buff.close()

    response = HttpResponse(ret_zip, mimetype="application/zip")
    response["Content-Disposition"] = "attachment; filename=%s.zip" % name
    return response

def reset_gjf(request):
    buff = StringIO()
    zfile = zipfile.ZipFile(buff, 'w', zipfile.ZIP_DEFLATED)

    for f in request.FILES.getlist('myfiles'):
        parser = fileparser.LogReset(f)

        name, _ = os.path.splitext(f.name)
        zfile.writestr("%s.gjf" % name, parser.format_output(errors=False))

    zfile.close()
    buff.flush()

    ret_zip = buff.getvalue()
    buff.close()

    response = HttpResponse(ret_zip, mimetype="application/zip")
    response["Content-Disposition"] = "attachment; filename=output.zip"
    return response
