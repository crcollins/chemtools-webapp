from cStringIO import StringIO
import zipfile
import os

from django.shortcuts import render
from django.template import Context
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper

from chemtools import fileparser, dataparser
import utils

def upload_data(request):
    switch = {
        "logparse": parse_log,
        "dataparse": parse_data,
        "gjfreset": reset_gjf,
    }
    error = None
    if request.method == "POST":
        if request.FILES.getlist('myfiles'):
            return switch[request.POST["option"]](request)
        else:
            error = "Please add some files."
    c = Context({
        "error_message": error
        })
    return render(request, "parse/upload_log.html", c)

def parse_log(request):
    parser = fileparser.LogSet()
    for f in utils.parse_file_list(request.FILES.getlist('myfiles')):
        parser.parse_file(f)

    f = StringIO(parser.format_output())
    response = HttpResponse(FileWrapper(f), content_type="text/plain")
    return response

def parse_data(request):
    buff = StringIO()
    zfile = zipfile.ZipFile(buff, 'w', zipfile.ZIP_DEFLATED)

    for i, f in enumerate(utils.parse_file_list(request.FILES.getlist('myfiles'))):
        parser = dataparser.DataParser(f)
        homolumo, gap = parser.get_graphs()

        name, _ = os.path.splitext(f.name)
        if i > 1:
            zfile.writestr(name + "/output.txt", parser.format_output())
            zfile.writestr(name + "/homolumo.eps", homolumo.getvalue())
            zfile.writestr(name + "/gap.eps", gap.getvalue())
        else:
            zfile.writestr("output.txt", parser.format_output())
            zfile.writestr("homolumo.eps", homolumo.getvalue())
            zfile.writestr("gap.eps", gap.getvalue())

    if i > 1:
        name = "output"
    zfile.close()
    buff.flush()

    ret_zip = buff.getvalue()
    buff.close()

    response = HttpResponse(ret_zip, mimetype="application/zip")
    response["Content-Disposition"] = "attachment; filename=%s.zip" % name
    return response

def reset_gjf(request):
    buff = StringIO()
    zfile = zipfile.ZipFile(buff, 'w', zipfile.ZIP_DEFLATED)

    for f in utils.parse_file_list(request.FILES.getlist('myfiles')):
        parser = fileparser.Log(f)

        name, _ = os.path.splitext(f.name)
        zfile.writestr("%s.gjf" % name, parser.format_gjf())

    zfile.close()
    buff.flush()

    ret_zip = buff.getvalue()
    buff.close()

    response = HttpResponse(ret_zip, mimetype="application/zip")
    response["Content-Disposition"] = "attachment; filename=output.zip"
    return response