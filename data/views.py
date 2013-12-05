import os

from django.shortcuts import render, redirect
from django.template import Context
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper

from chemtools.utils import CLUSTERS, CLUSTER_TUPLES


def frag_index(request):
    data = (
        ["Cores", ("CON", "TON", "TSN", "CSN", "TNN", "CNN", "CCC", "TCC")],
        ["X Groups", (["A", "H"], ["B", "Cl"], ["C", "Br"], ["D", "CN"], ["E", "CCH"],
            ["F", "OH"], ["G", "SH"], ["H", "NH_2"], ["I", "CH_3"], ["J", "phenyl"], ["K", "TMS"],
             ["L", "OCH_3"])],
        ["Aryl Groups", (["2", "double"], ["3", "triple"], ["4", "phenyl"], ["5", "thiophene"],
            ["6", "pyridine"], ["7", "carbazole"], ["8", "TZ"], ["9", "EDOT"])],
        ["R Groups", (["a", "H"], ["b", "Cl"], ["c", "Br"], ["d", "CN"], ["e", "CCH"],
            ["f", "OH"], ["g", "SH"], ["h", "NH_2"], ["i", "CH_3"], ["j", "phenyl"], ["k", "TMS"],
             ["l", "OCH_3"])],
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
