from django.shortcuts import render, redirect
from django.template import Context
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.utils import simplejson

from account.utils import add_account_page, PAGES
from models import Job, CredentialForm, ClusterForm, Cluster, Credential
import interface
from utils import get_credentials_from_request


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
    cluster = request.REQUEST.get("cluster", "")
    jobs = interface.get_all_jobs(request.user, cluster)
    a = {
        "is_authenticated": request.user.is_authenticated(),
        "clusters": jobs,
    }
    if request.REQUEST.get("html", ''):
        c = Context(a)
        return render(request, "cluster/job_table.html", c)
    return HttpResponse(simplejson.dumps(a), mimetype="application/json")


@login_required
def job_detail(request, cluster, jobid):
    credential = Credential.objects.get(user=request.user, cluster__name=cluster)
    results = interface.get_specific_jobs(credential, [jobid])
    if results["error"]:
        e = results["error"]
        job = None
    elif results["failed"]:
        e = results["failed"][0][1]
        job = None
    else:
        job = results["worked"][0][1]
        e = None
    c = Context({
        "job": job,
        "cluster": cluster,
        "error_message": e,
        })
    return render(request, "cluster/job_detail.html", c)


@login_required
def kill_job(request, cluster):
    if request.method != "POST":
        return redirect(job_index)

    jobids = []
    for key in request.POST:
        try:
            int(key)
            jobids.append(key)
        except ValueError:
            pass
    credential = Credential.objects.get(user=request.user, cluster__name=cluster)
    result = interface.kill_jobs(credential, jobids)
    if result["error"] is None:
        return redirect(job_index)
    else:
        return HttpResponse(result["error"])


@login_required
@add_account_page("credentials")
def credential_settings(request, username):
    state = "Change Settings"
    initial = {"username": request.user.get_profile().xsede_username}
    working_creds = []
    failing_creds = []
    if request.method == "POST":
        if "delete" in request.POST:
            form = CredentialForm(request.user, initial=initial)
            for cred in get_credentials_from_request(request):
                cred.delete()
            state = "Settings Successfully Saved"

        elif "test" in request.POST:
            form = CredentialForm(request.user, initial=initial)
            for cred in get_credentials_from_request(request):
                if cred.connection_works():
                    working_creds.append(cred)
                else:
                    failing_creds.append(cred)

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
        "pages": PAGES,
        "page": "credentials",
        "state": state,
        "form": form,
        "failing_creds": failing_creds,
        "working_creds": working_creds,
        })
    return render(request, "cluster/credential_settings.html", c)


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
        "pages": PAGES,
        "page": "clusters",
        "state": state,
        "form": form,
        "clusters": Cluster.objects.all(),
        })
    return render(request, "cluster/cluster_settings.html", c)
