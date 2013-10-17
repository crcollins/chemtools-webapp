from django.shortcuts import render
from django.template import Context
import misaka

import utils

def index(request):
    a = "".join(open("README.md", "r").readlines())
    headerend = a.index("Build")
    bodystart = a.index("_" * 71 + "\nNaming")
    tree = misaka.html(a[bodystart:], render_flags=misaka.HTML_TOC_TREE)
    body = misaka.html(a[bodystart:], render_flags=misaka.HTML_TOC)
    c = Context({
        "header": misaka.html(a[:headerend]),
        "toc": utils.postprocess_toc(tree, "#"),
        "docs": utils.postprocess_toc(body, 'id="'),
        })
    return render(request, "docs/index.html", c)

def common_errors(request):
    a = "".join(open("docs/other/common_errors.md", "r").readlines())
    c = Context({
        "docs": misaka.html(a),
        })
    return render(request, "docs/content.html", c)

def one_liners(request):
    a = "".join(open("docs/other/one_liners.md", "r").readlines())
    c = Context({
        "docs": misaka.html(a),
        })
    return render(request, "docs/content.html", c)