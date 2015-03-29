import os
import re

from django.core.management.base import BaseCommand
from django.template import loader, Context
import misaka

from docs.utils import postprocess_toc


class Command(BaseCommand):
    args = ''
    help = 'Make static pages for the docs'

    def handle(self, *args, **options):
        names = os.listdir("docs/other")
        paths = [os.path.join("docs/other", x) for x in names]
        paths += ["README.md"]

        for path in paths:
            text = "".join(open(path, "r").readlines())

            if path.endswith("_plain.md"):
                c = Context({
                    "docs": misaka.html(text),
                })
                t = loader.get_template("docs/content.html")
                page = os.path.split(path)[1].replace("_plain.md", ".html")
            else:
                tree = misaka.html(text, render_flags=misaka.HTML_TOC_TREE)
                body = misaka.html(text, render_flags=misaka.HTML_TOC)

                c = Context({
                    "toc": postprocess_toc(tree, "#"),
                    "docs": postprocess_toc(body, 'id="'),
                })
                t = loader.get_template("docs/index.html")
                page = os.path.split(path)[1].replace(".md", ".html")

            page = page.replace("README", "technical")

            with open(os.path.join("docs/static/docs", page), "w") as f:
                rendered = t.render(c)
                f.write(rendered)

