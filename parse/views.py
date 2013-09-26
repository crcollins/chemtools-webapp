import zipfile
import os
import re

from django.shortcuts import render
from django.template import Context
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper

from chemtools import fileparser, dataparser
from chem.utils import StringIO
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

def _find_sets(files):
    logs = []
    datasets = []
    for f in files:
        if f.name.endswith(".log"):
            logs.append(f)
        else:
            datasets.append(f)

    logsets = {}
    for f in logs:
        nums = re.findall(r'n(\d+)', f.name)
        if not nums:
            continue
        num = nums[-1]

        name = f.name.replace(".log", '').replace("n%s" % num, '')
        if name in logsets.keys():
            logsets[name].append((num,f))
        else:
            logsets[name] = [(num,f)]
    return logsets, datasets


def _convert_logs(logsets):
    converted = []
    for key in logsets:
        nvals = []
        homovals = []
        lumovals = []
        gapvals = []
        for num, log in logsets[key]:
            parser = fileparser.Log(log)

            nvals.append(num)
            homovals.append(parser["Occupied"])
            lumovals.append(parser["Virtual"])
            gapvals.append(parser["Excited"])

        f = StringIO(key)
        f.write(', '.join(nvals)+"\n")
        f.write(', '.join(homovals)+"\n")
        f.write(', '.join(lumovals)+"\n")
        f.write(', '.join(gapvals)+"\n")
        f.seek(0)
        converted.append(f)
    return converted

def parse_data(request):
    buff = StringIO()
    zfile = zipfile.ZipFile(buff, 'w', zipfile.ZIP_DEFLATED)
    files = list(utils.parse_file_list(request.FILES.getlist('myfiles')))

    logsets, files = _find_sets(files)
    files.extend(_convert_logs(logsets))

    num = len(files)
    for f in files:
        parser = dataparser.DataParser(f)
        homolumo, gap = parser.get_graphs()

        name, _ = os.path.splitext(f.name)
        if num > 1:
            zfile.writestr(name + "/output.txt", parser.format_output())
            zfile.writestr(name + "/homolumo.eps", homolumo.getvalue())
            zfile.writestr(name + "/gap.eps", gap.getvalue())
        else:
            zfile.writestr("output.txt", parser.format_output())
            zfile.writestr("homolumo.eps", homolumo.getvalue())
            zfile.writestr("gap.eps", gap.getvalue())

    if num > 1:
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
