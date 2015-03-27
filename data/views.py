import os

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper
from django.contrib.auth.decorators import login_required

from chemtools.extractor import CORES, RGROUPS, ARYL
from data.models import JobTemplate
from data.forms import JobTemplateForm
from account.utils import add_account_page, PAGES


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
    c = {
        "pages": PAGES,
        "page": "templates",
        "templates": JobTemplate.get_templates(request.user),
        "form": JobTemplateForm(),
    }
    return render(request, "data/template_settings.html", c)
