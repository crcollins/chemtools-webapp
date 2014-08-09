import os
import re
import threading

from models import Job
from utils import get_ssh_connection_obj, get_sftp_connection_obj, _run_job, \
                _get_jobs, add_fileparser


def run_job(credential, gjfstring, jobstring=None, **kwargs):
    results = {
        "jobid": None,
        "error": None,
    }
    try:
        results["cluster"] = credential.cluster.name
        if not credential.user.is_staff:
            results["error"] = "You must be a staff user to submit a job."
            return results
        ssh = get_ssh_connection_obj(credential)
        sftp = get_sftp_connection_obj(credential)
    except:
        results["error"] = "Invalid credential"
        results["cluster"] = None
        return results

    with ssh, sftp:
        temp = _run_job(ssh, sftp, gjfstring, jobstring, **kwargs)
        results["jobid"] = temp[0]
        results["error"] = temp[1]
        return results


def run_jobs(credential, names, gjfstrings, jobstring=None, **kwargs):
    results = {
        "worked": [],
        "failed": [],
        "error": None,
    }
    try:
        results["cluster"] = credential.cluster.name
        if not credential.user.is_staff:
            results["error"] = "You must be a staff user to submit a job."
            return results
        ssh = get_ssh_connection_obj(credential)
        sftp = get_sftp_connection_obj(credential)
    except:
        results["error"] = "Invalid credential"
        results["cluster"] = None
        return results

    with ssh, sftp:
        for name, gjf in zip(names, gjfstrings):
            dnew = kwargs.copy()
            dnew["name"] = re.sub(r"{{\s*name\s*}}", name, dnew.get("name", ''))
            temp = _run_job(ssh, sftp, gjf, jobstring, **dnew)
            if temp[1] is None:
                results["worked"].append((name, temp[0]))
            else:
                results["failed"].append((name, temp[1]))
    return results


def kill_jobs(credential, jobids):
    results = {
        "worked": [],
        "failed": [],
        "error": None,
    }
    try:
        results["cluster"] = credential.cluster.name
        if not credential.user.is_staff:
            results["error"] = "You must be a staff user to kill a job."
            return results
        ssh = credential.get_ssh_connection()
    except:
        results["error"] = "Invalid credential"
        results["cluster"] = None
        return results

    with ssh:
        specfic_results = get_specific_jobs(credential, jobids)

        results["failed"] = specfic_results["failed"]
        for (jobid, job_data) in specfic_results["worked"]:
            _, _, stderr = ssh.exec_command("qdel %s" % jobid)
            b = stderr.readlines()
            if b:
                results["failed"].append((jobid, str(b)))
                continue

            try:
                job = Job.objects.filter(jobid=jobid)[0]
                job.delete()
            except IndexError:
                pass
            results["worked"].append(jobid)
    return results


def get_all_jobs(user, cluster=None):
    if cluster:
        creds = user.credentials.filter(cluster__name__iexact=cluster)
    else:
        creds = user.credentials.all()

    threads = []
    # results is a mutable object, so as the threads complete they save their
    # results into this object. This method is used in lieu of messing with
    # multiple processes
    results = [None] * len(creds)
    for i, cred in enumerate(creds):
        t = threading.Thread(target=_get_jobs,
                            args=(cred, cred.cluster.name, i, results))
        t.start()
        threads.append(t)

    for t in threads:
        t.join(20)
    return [x for x in results if x]


def get_specific_jobs(credential, jobids):
    results = {
        "worked": [],
        "failed": [],
        "error": None,
    }
    try:
        results["cluster"] = credential.cluster.name
        ssh = credential.get_ssh_connection()
    except:
        results["error"] = "Invalid credential"
        results["cluster"] = None
        return results

    if not jobids:
        return results

    all_jobs = get_all_jobs(credential.user, credential.cluster.name)
    cluster_jobs = all_jobs[0]

    running_jobs = cluster_jobs["jobs"]
    running_jobids = [x[0] for x in cluster_jobs["jobs"]]

    for job in jobids:
        if job not in running_jobids:
            pair = (job, "That job number is not running.")
            results["failed"].append(pair)
            continue
        else:
            pair = (job, running_jobs[running_jobids.index(job)])
            results["worked"].append(pair)
    return results


def get_all_log_data(credential):
    results = {
        "results": None,
        "error": None,
    }
    try:
        results["cluster"] = credential.cluster.name
        ssh = credential.get_ssh_connection()
        sftp = credential.get_sftp_connection()
    except:
        results["error"] = "Invalid credential"
        results["cluster"] = None
        return results

    with ssh, sftp:
        err = add_fileparser(ssh, sftp)
        if err:
            results["error"] = err
            return results

        command = "python chemtools/fileparser.py -L -f chemtools/done"
        _, stdout, stderr = ssh.exec_command(command)

        if err:
            results["error"] = err
            return results

        results["results"] = stdout.read()
    return results

def get_log_data(credential, names):
    results = {
        "results": None,
        "error": None,
    }
    try:
        results["cluster"] = credential.cluster.name
        ssh = credential.get_ssh_connection()
        sftp = credential.get_sftp_connection()
    except:
        results["error"] = "Invalid credential"
        results["cluster"] = None
        return results

    with ssh, sftp:
        err = add_fileparser(ssh, sftp)
        if err:
            results["error"] = err
            return results

        # this is partially for security, and partially to not just give the
        # file parser a massive block of filenames.
        # TODO: Make this thread safe
        with sftp.open("chemtools/files", 'w') as f:
            for filename in names:
                f.write('chemtools/done/%s.log\n' % filename)

        command = "python chemtools/fileparser.py -L -i chemtools/files"
        _, stdout, stderr = ssh.exec_command(command)

        err = stderr.read()
        if err:
            results["error"] = err
            return results

        results["results"] = stdout.read()
    return results


def get_log_status(credential, names):
    results = {
        "results": None,
        "error": None,
    }
    try:
        results["cluster"] = credential.cluster.name
        ssh = credential.get_ssh_connection()
        sftp = credential.get_sftp
    except:
        results["error"] = "Invalid credential"
        results["cluster"] = None
        return results

    with ssh, sftp:
        err = add_fileparser(ssh, sftp)
        if err:
            results["error"] = err
            return results

        status = []
        for name in names:
            path = "chemtools/done/%s" % name
            # TODO: Make this safer
            _, stdout, stderr = ssh.exec_command("tail -n1 " + path)
            if "Normal termination of Gaussian" in stdout.read():
                status.append(Job.COMPLETED)
            elif "tail: cannot open" % path in stderr.read():
                # continue # no file
                # might be walltime
                status.append(Job.WALLTIME)
            else:
                status.append(Job.FAILED)
            results["results"] = status
    return results
