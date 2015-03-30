import os

from django.shortcuts import render
from django.conf import settings
from django.http import Http404


def index(request):
    path = os.path.join(settings.STATIC_ROOT, "docs", "main.html")
    c = {
        "content": open(path, "r").read(),
    }
    return render(request, "docs/final.html", c)


def docs_pages(request, page):
    base = os.path.join(settings.STATIC_ROOT, "docs")
    pages = [x.replace(".html", "") for x in os.listdir(base)]

    if page not in pages:
        raise Http404

    path = os.path.join(settings.STATIC_ROOT, "docs", "%s.html" % page)
    c = {
        "content": open(path, "r").read(),
    }
    return render(request, "docs/final.html", c)
