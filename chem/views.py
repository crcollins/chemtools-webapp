from cStringIO import StringIO
import zipfile
import os

from django.shortcuts import render, redirect
from django.template import Context, RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.core.servers.basehttp import FileWrapper
from django.contrib.auth.decorators import login_required
import paramiko

from models import ErrorReport, ErrorReportForm, JobForm, LogForm
import gjfwriter
import fileparser
import utils


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

    errors = []
    warnings = []
    for mol in molecules.split(','):
        try:
            gjfwriter.parse_name(mol)
            errors.append(None)
        except Exception as e:
            errors.append(e)
        warnings.append(ErrorReport.objects.filter(molecule=mol))

    c = Context({
        "molecules": zip(molecules.split(','), errors, warnings),
        "pagename": molecules,
        "basis": basis
        })
    return render(request, "chem/multi_detail.html", c)

def gen_multi_detail_zip(request, molecules):
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
    for x in ("name", "email", "nodes", "ncpus", "time", "cluster"):
        if request.GET.get(x):
            a[x] = request.GET[x]
    if a:
        form = JobForm(request.GET, initial=a)
        if form.is_valid():
            return HttpResponse(utils.write_job(**a), content_type="text/plain")
    else:
        if request.user.is_authenticated():
            email = request.user.email
        else:
            email = ""
        form = JobForm(initial={"name": molecule, "email": email})

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

def job_index(request):
    try:
        jobs = utils.get_all_jobs()
        e = None
    except Exception as e:
        pass
    c = Context({
        "jobs": jobs,
        "error_message": e,
        })
    return render(request, "chem/job_index.html", c)

def job_multi_detail(request, jobids):
    jobids = jobids.split(',')

    jobs = []
    for job in utils.get_all_jobs():
        if job[0] in jobids:
            jobs.append(job)
    e = None
    c = Context({
        "jobs":jobs,
        "error_message": e,
        })
    return render(request, "chem/job_index.html", c)

@login_required
def run_molecule(request, molecule):
    if not request.user.is_staff:
        return HttpResponse("You must be a staff user to submit a job.")

    if request.method == "POST":
        d = request.POST.dict()
        if "basis" not in d:
            d["basis"] = ''
        jobid, e = utils.start_run_molecule(molecule, **d)
        if e is None:
            return HttpResponse("It worked. Your job id is: %d" % jobid)
        else:
            return HttpResponse(e)
    else:
        return redirect(get_job, molecule)

@login_required
def reset_job(request, jobid):
    """Used to restart jobs that have hit the time limit."""
    if not request.user.is_staff:
        return HttpResponse("You must be a staff user to reset a job.")

    if request.method == "POST":
        e = None
        # d = request.GET.dict()
        # jobid, e = utils.start_run_molecule(molecule, **d)
        if e is None:
            return HttpResponse("It worked. Your job id is: %s" % jobid)
        else:
            return HttpResponse(e)
