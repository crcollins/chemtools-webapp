from django.shortcuts import render
import misaka

import utils


def index(request):
    a = "".join(open("docs/other/main.md", "r").readlines())

    tree = misaka.html(a, render_flags=misaka.HTML_TOC_TREE)
    body = misaka.html(a, render_flags=misaka.HTML_TOC)
    c = {
        # "header": misaka.html(a),
        "toc": utils.postprocess_toc(tree, "#"),
        "docs": utils.postprocess_toc(body, 'id="'),
    }
    return render(request, "docs/index.html", c)


def common_errors(request):
    a = "".join(open("docs/other/common_errors.md", "r").readlines())
    c = {
        "docs": misaka.html(a),
    }
    return render(request, "docs/content.html", c)


def one_liners(request):
    a = "".join(open("docs/other/one_liners.md", "r").readlines())
    c = {
        "docs": misaka.html(a),
    }
    return render(request, "docs/content.html", c)


def technical(request):
    a = "".join(open("README.md", "r").readlines())
    c = {
        "docs": misaka.html(a),
    }
    return render(request, "docs/content.html", c)


def resources(request):
    a = "".join(open("docs/other/resources.md", "r").readlines())
    c = {
        "docs": misaka.html(a),
    }
    return render(request, "docs/content.html", c)
