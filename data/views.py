import os

from django.shortcuts import render, redirect
from django.template import Context
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper

from chemtools.constants import CLUSTERS, CLUSTER_TUPLES
from chemtools.extractor import CORES, RGROUPS, ARYL


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
    data = [CLUSTERS[x] for x in CLUSTERS.keys()]
    c = Context({"templates": data})
    return render(request, "data/template_index.html", c)


def get_template(request, template):
    template = template.lower()
    if template in [x.lower() for x in sum(CLUSTER_TUPLES, ())]:
        letter = template[0]
        f = open("chemtools/templates/chemtools/%sjob.txt" % letter)
        response = HttpResponse(FileWrapper(f), content_type="text/plain")
    else:
        response = HttpResponse('', content_type="text/plain")
    return response
