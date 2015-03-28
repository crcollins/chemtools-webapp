import os
import logging

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper
from django.contrib.auth.decorators import login_required

from chemtools.extractor import CORES, RGROUPS, ARYL
from data.models import JobTemplate
from data.forms import JobTemplateForm
from account.utils import add_account_page, PAGES
from utils import get_templates_from_request


logger = logging.getLogger(__name__)


def frag_index(request):
    xrnames = ["Hydrogen", "Chlorine", "Bromine", "Cyano", "Alkyne", "Hydroxy",
               "Thiol", "Amine", "Methyl", "Phenyl", "TMS", "Methoxy", "Fluorine"]
    arylnames = ["double bond", "triple bond", "tetrazine", "EDOT", "DTF",
                 "acetyl", "phenyl", "thiophene", "pyridine", "carbazole",
                 "furan", "pyrrole"]
    data = (
        ["Cores", CORES],
        ["X/R Groups", zip(RGROUPS, xrnames)],
        ["Aryl Groups", zip(ARYL, arylnames)],
    )
    c = {"usable_parts": data}
    return render(request, "data/frag_index.html", c)


def get_frag(request, frag):
    if frag in os.listdir("chemtools/data/"):
        f = open("chemtools/data/" + frag, "r")
        response = HttpResponse(FileWrapper(f), content_type="text/plain")
        return response
    else:
        return redirect(frag_index)


def template_index(request):
    c = {"templates": JobTemplate.objects.all()}
    return render(request, "data/template_index.html", c)


@login_required
@add_account_page("templates")
def template_settings(request, username):
    state = "Change Settings"

    if request.method == "POST":
        if "delete" in request.POST:
            i = 0
            for i, template in enumerate(get_templates_from_request(request)):
                template.delete()
            logger.info("%s deleted %d template(s)" % (username, i+1))
            state = "Settings Successfully Saved"
            form = JobTemplateForm(request.user)

        elif "save" in request.POST:
            form = JobTemplateForm(request.user, request.POST)
            if form.is_valid():
                try:
                    name = form.cleaned_data.get("name")
                    obj = JobTemplate.objects.get(creator=request.user, name=name)
                    with open(a.template.path, "w") as f:
                        f.write(form.cleaned_data.get("template"))

                except JobTemplate.DoesNotExist:
                    obj = form.save(commit=False)
                    obj.creator = request.user
                    obj.save()
                state = "Settings Successfully Saved"
                form = JobTemplateForm(request.user)

    else:
        form = JobTemplateForm(request.user)

    c = {
        "pages": PAGES,
        "page": "templates",
        "state": state,
        "form": form,
        "templates": JobTemplate.get_templates(request.user),
    }
    return render(request, "data/template_settings.html", c)
