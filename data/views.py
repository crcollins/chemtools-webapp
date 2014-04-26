import os

from django.shortcuts import render, redirect
from django.template import Context
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper

from chemtools.extractor import CORES, RGROUPS, ARYL
from data.models import JobTemplate

def frag_index(request):
    xrnames = ["H", "Cl", "Br", "CN", "CCH", "OH",
            "SH", "NH_2", "CH_3", "phenyl", "TMS", "OCH_3"]
    arylnames = ["double bond", "triple bond", "phenyl",
                "thiophene", "pyridine", "carbazole", "TZ", "EDOT"]
    data = (
        ["Cores", CORES],
        ["X/R Groups", zip(RGROUPS, xrnames)],
        ["Aryl Groups", zip(ARYL, arylnames)],
    )
    c = Context({"usable_parts": data})
    return render(request, "data/frag_index.html", c)


def get_frag(request, frag):
    if frag in os.listdir("chemtools/data/"):
        f = open("chemtools/data/" + frag, "r")
        response = HttpResponse(FileWrapper(f), content_type="text/plain")
        return response
    else:
        return redirect(frag_index)


def template_index(request):
    c = Context({"templates": JobTemplate.objects.all()})
    return render(request, "data/template_index.html", c)
