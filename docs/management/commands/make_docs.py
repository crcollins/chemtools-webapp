import os
import re

from django.core.management.base import BaseCommand
from django.template import loader, Context
from django.test import Client
import misaka

from docs.utils import postprocess_toc


class Command(BaseCommand):
    args = ''
    help = 'Make static pages for the docs'

    def handle(self, *args, **options):
        names = os.listdir("docs/other")
        paths = [os.path.join("docs/other", x) for x in names]
        paths += ["README.md"]

        mkdir_p("docs/static/docs/img")

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
                new_rendered = self.get_and_replace_images(rendered)
                f.write(new_rendered)

    def get_and_replace_images(self, text):
        image_urls = set(re.findall('<img src="(.*?)"', text))
        c = Client()

        for image_url in image_urls:
            name = os.path.split(image_url)[1]
            request = c.get(image_url)
            with open(os.path.join("docs/static/docs/img", name), "w") as f:
                f.write(request.content)

            new_url = os.path.join("img", name)
            text = text.replace(image_url, new_url)
        return text


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        import errno
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise