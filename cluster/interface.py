import os
import re
import threading

from chemtools import gjfwriter
from chemtools import fileparser
from chemtools.mol_name import name_expansion

from models import Job
from utils import get_ssh_connection_obj, get_sftp_connection_obj, _run_job, _get_jobs


def run_job(credential, gjfstring, jobstring=None, **kwargs):
    ssh = get_ssh_connection_obj(credential)
    sftp = get_sftp_connection_obj(credential)

    results = {"jobid": None, "error": None, "cluster": credential.cluster.name}
    if not credential.user.is_staff:
        results["error"] = "You must be a staff user to submit a job."
        return results

    with ssh, sftp:
        temp = _run_job(ssh, sftp, gjfstring, jobstring, **kwargs)
        results["jobid"] = temp[0]
        results["error"] = temp[1]
        return results


def run_jobs(credential, names, gjfstrings, jobstring=None, **kwargs):
    ssh = get_ssh_connection_obj(credential)
    sftp = get_sftp_connection_obj(credential)

    results = {
        "worked": [],
        "failed": [],
        "error": None,
        "cluster": credential.cluster.name,
    }
    if not credential.user.is_staff:
        results["error"] = "You must be a staff user to submit a job."
        return results

    with ssh, sftp:
        for name, gjf in zip(names, gjfstrings):
            dnew = kwargs.copy()
            dnew["name"] = re.sub(r"{{\s*name\s*}}", name, dnew["name"])
            temp = _run_job(ssh, sftp, gjf, jobstring, **dnew)
            if temp[1] is None:
                results["worked"].append((name, temp[0]))
            else:
                results["failed"].append((name, temp[1]))
    return results


def run_standard_job(credential, molecule, **kwargs):
    results = {"jobid": None, "error": None, "cluster": credential.cluster.name}
    try:
        out = gjfwriter.GJFWriter(molecule, kwargs.get("keywords", None))
    except Exception as e:
        results["error"] = str(e)
        return results

    gjf = out.get_gjf()
    results = run_job(credential, gjf, **kwargs)
    # if results["error"] is None:
    #     job = Job(molecule=molecule, jobid=results["jobid"], **kwargs)
    #     job.save()
    return results


def run_standard_jobs(credential, string, **kwargs):
    results = {
        "worked": [],
        "failed": [],
        "error": None,
        "cluster": credential.cluster.name,
    }
    if not credential.user.is_staff:
        results["error"] = "You must be a staff user to submit a job."
        return results

    names = []
    gjfs = []
    for mol in name_expansion(string):
        try:
            out = gjfwriter.GJFWriter(mol, kwargs.get("keywords", None))
        except Exception as e:
            results["failed"].append((mol, str(e)))
            continue

        names.append(mol)
        gjfs.append(out.get_gjf())

    temp = run_jobs(credential, names, gjfs, **kwargs)
    results["worked"] = temp["worked"]
    results["failed"].extend(temp["failed"])
    results["error"] = temp["error"]
    return results


def kill_jobs(user, cluster, jobids):
    cred = user.credentials.filter(cluster__name=cluster)[0]
    results = {
        "worked": [],
        "failed": [],
        "error": None,
        "cluster": cred.cluster.name,
    }
    if not user.is_staff:
        results["error"] = "You must be a staff user to submit a job."
        return results

    ssh = cred.get_ssh_connection()
    with ssh:
        a = get_all_jobs(user, cluster)

        if not a:
            results["error"] = "There are no jobs running."
            return results

        jobs = [x[0] for x in a[0]["jobs"]]
        for jobid in jobids:
            if jobid not in jobs:
                results["failed"].append((jobid, "That job number is not running."))
                continue

            _, _, stderr = ssh.exec_command("qdel %s" % jobid)
            b = stderr.readlines()
            if not b:
                results["failed"].append((jobid, str(b)))
                continue

            try:
                job = Job.objects.filter(jobid=jobid)[0]
                job.delete()
            except IndexError:
                pass
    return results


def get_all_jobs(user, cluster=None):
    if cluster:
        creds = user.credentials.filter(cluster__name__iexact=cluster)
    else:
        creds = user.credentials.all()

    threads = []
    # results is a mutable object, so as the threads complete they save their results into this object
    # this method is used in lieu of messing with multiple processes
    results = [None] * len(creds)
    for i, cred in enumerate(creds):
        t = threading.Thread(target=_get_jobs, args=(cred, cred.cluster.name, i, results))
        t.start()
        threads.append(t)

    for t in threads:
        t.join(20)
    return [x for x in results if x]
