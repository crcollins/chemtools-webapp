from django.shortcuts import render, redirect
from django.template import Context
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import simplejson

from models import Job, CredentialForm
import utils


@login_required
def job_index(request):
    return render(request, "cluster/job_index.html")

@login_required
def cred_index(request):
    if request.method == "POST":
        form = CredentialForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            form = CredentialForm()
    else:
        form = CredentialForm()

    c = Context({
        "form": form,
        })
    return render(request, "cluster/cred_index.html", c)

@login_required
def get_job_list(request):
    try:
        jobs = utils.get_all_jobs(request.user)
        e = None
    except Exception as e:
        jobs = []
    a = {
        "is_authenticated": request.user.is_authenticated(),
        "jobs": jobs,
    }
    return HttpResponse(simplejson.dumps(a), mimetype="application/json")

@login_required
def job_detail(request, jobid):
    e = None
    for job in utils.get_all_jobs(request.user):
        if job[0] == jobid:
            break
    else:
        job = None
        e = "That job number is not running."
    c = Context({
        "job": job,
        "error_message": e,
        })
    return render(request, "cluster/job_detail.html", c)

@login_required
def reset_job(request, jobid):
    """Used to restart jobs that have hit the time limit."""
    if not request.user.is_staff:
        return HttpResponse("You must be a staff user to reset a job.")

    if request.method == "POST":
        e = None
        name = Job.objects.filter(jobid=jobid).name
        njobid, e = utils.reset_output(request.user, name)
        if e is None:
            return HttpResponse("It worked. Your new job id is: %d" % njobid)
        else:
            return HttpResponse(e)

@login_required
def kill_job(request, jobid):
    if not request.user.is_staff:
        return HttpResponse("You must be a staff user to kill a job.")

    if request.method == "POST":
        e = utils.kill_job(request.user, jobid)
        if e is None:
            try:
                job = Job.objects.filter(jobid=jobid)[0]
                job.delete()
            except IndexError:
                pass
            return redirect(job_index)
        else:
            return HttpResponse(e)
