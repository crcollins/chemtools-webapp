from django.shortcuts import render, redirect
from django.template import Context
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import simplejson

from account.utils import add_account_page
from models import Job, CredentialForm, ClusterForm, Cluster
import interface


@login_required
def job_index(request):
    return render(request, "cluster/job_index.html")


@login_required
def cluster_job_index(request, cluster):
    c = Context({
        "cluster": cluster,
        })
    return render(request, "cluster/job_index.html", c)


@login_required
def get_job_list(request):
    try:
        cluster = request.REQUEST.get("cluster", "")
        jobs = interface.get_all_jobs(request.user, cluster)
        e = None
    except Exception as e:
        jobs = []
    a = {
        "is_authenticated": request.user.is_authenticated(),
        "clusters": jobs,
    }
    return HttpResponse(simplejson.dumps(a), mimetype="application/json")


@login_required
def job_detail(request, cluster, jobid):
    e = None
    jobs = interface.get_all_jobs(request.user, cluster)[0]
    for job in jobs["jobs"]:
        if job[0] == jobid:
            break
    else:
        job = None
        e = "That job number is not running."
    c = Context({
        "job": job,
        "cluster": cluster,
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
        njobid, e = interface.reset_output(request.user, name)
        if e is None:
            return HttpResponse("It worked. Your new job id is: %d" % njobid)
        else:
            return HttpResponse(e)


@login_required
def kill_job(request, cluster):
    if not request.user.is_staff:
        return HttpResponse("You must be a staff user to kill a job.")

    if request.method == "POST":
        jobids = []
        for key in request.POST:
            try:
                int(key)
                jobids.append(key)
            except ValueError:
                pass
        result = interface.kill_jobs(request.user, cluster, jobids)
        if result["error"] is None:
            return redirect(job_index)
        else:
            return HttpResponse(e)
    else:
        return redirect(job_index)


@login_required
@add_account_page("credentials")
def credential_settings(request, username):
    state = "Change Settings"
    initial = {"username": request.user.get_profile().xsede_username}
    if request.method == "POST":
        if "delete" in request.POST:
            form = CredentialForm(request.user, initial=initial)
            usercreds = request.user.credentials.all()
            for key in request.POST:
                if "@" in key and request.POST[key] == "on":
                    username, hostname = key.split("@")
                    try:
                        usercreds.get(username=username, cluster__hostname=hostname).delete()
                    except:
                        pass
        else:
            form = CredentialForm(request.user, request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.user = request.user
                obj.save()
                state = "Settings Successfully Saved"
                form = CredentialForm(request.user, initial=initial)
    else:
        form = CredentialForm(request.user, initial=initial)

    c = Context({
        "pages": utils.PAGES,
        "page": "credentials",
        "state": state,
        "form": form,
        })
    return render(request, "account/credential_settings.html", c)


@login_required
@add_account_page("clusters")
def cluster_settings(request, username):
    state = "Change Settings"
    if request.method == "POST":
        form = ClusterForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            state = "Settings Successfully Saved"
            form = ClusterForm()
    else:
        form = ClusterForm()

    c = Context({
        "pages": utils.PAGES,
        "page": "clusters",
        "state": state,
        "form": form,
        "clusters": Cluster.objects.all(),
        })
    return render(request, "account/cluster_settings.html", c)