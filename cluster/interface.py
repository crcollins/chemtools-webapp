import os
import re
import threading

from chemtools import gjfwriter
from chemtools import fileparser
from chemtools.utils import name_expansion

from models import Job
from utils import get_ssh_connection, get_sftp_connection, _run_job, _get_jobs, get_compressed_file

def run_job(credential, gjfstring, jobstring=None, **kwargs):
    ssh = get_ssh_connection(credential)
    sftp = get_sftp_connection(credential)

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
    ssh = get_ssh_connection(credential)
    sftp = get_sftp_connection(credential)

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
        t = threading.Thread(target=_get_jobs, args=(cred, i, results))
        t.start()
        threads.append(t)

    for t in threads:
        t.join(20)
    return [x for x in results if x]

def recover_output(user, name):
    with ssh, sftp:
        _, stdout, stderr = ssh.exec_command("ls done/%s.*" % name)
        files = [x.replace("\n", "").lstrip("done/") for x in stdout.readlines()]

        err = stderr.readlines()
        if err:
            return err

        for fname in files:
            if fname.endswith(".log"):  # only download log files for now
                path = os.path.join("done/", fname)
                f, err, zippath = get_compressed_file(ssh, sftp, path)
                with open(fname, "w") as f2, f:
                    for line in f:
                        f2.write(line)
                ssh.exec_command("rm %s %s" % (zippath, path + ".bak"))

def reset_output(user, name):
    '''If successful this is successful, it will start the file that was reset,
    and it will leave the old backup file. Otherwise, it will return to the
    original state.
    '''
    with ssh, sftp:
        fpath = ''.join([os.path.join("test", name), '.log'])
        jobpath = ''.join([os.path.join("test", name), '.gjob'])
        fbakpath = fpath + ".bak"

        f, err, zippath = get_compressed_file(ssh, sftp, fpath)
        if f:
            with f:
                parser = fileparser.LogReset(f, fpath)
                ssh.exec_command("rm %s" % zippath)
        else:
            return None, err

        f2 = sftp.open(fpath, "w")
        f2.write(parser.format_output(errors=False))
        f2.close()

        _, stdout, stderr = ssh.exec_command("qsub %s" % jobpath)
        err = stderr.readlines()
        if err:
            ssh.exec_command("mv {0} {1}".format(fbakpath, fpath))
            return None, err

        e = None
        try:
            jobid = stdout.readlines()[0].split('.')[0]
        except Exception as e:
            jobid = None
    return jobid, e
