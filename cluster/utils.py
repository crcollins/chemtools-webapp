import os
import bz2
import time
import re
import threading

from chemtools import gjfwriter
from chemtools import fileparser
from chemtools.utils import name_expansion, write_job
from project.utils import StringIO, SSHClient, SFTPClient

from models import Credential, Job

def get_ssh_connection(obj):
    if isinstance(obj, Credential):
        try:
            return obj.get_ssh_connection()
        except: # sometimes this timesout
            return obj.get_ssh_connection()
    elif isinstance(obj, SSHClient):
        return obj
    else:
        raise TypeError

def get_sftp_connection(obj):
    if isinstance(obj, Credential):
        try:
            return obj.get_sftp_connection()
        except: # sometimes this timesout
            return obj.get_sftp_connection()
    elif isinstance(obj, SFTPClient):
        return obj
    else:
        raise TypeError

def _make_folders(ssh):
    folder = 'chemtools/done/'
    _, _, testerr2 = ssh.exec_command("mkdir -p %s" % folder)
    testerr2 = testerr2.readlines()
    if testerr2:
        return testerr2[0]
    return None

def _run_job(ssh, sftp, gjfstring, jobstring=None, **kwargs):
    try:
        error = _make_folders(ssh)
        if error:
            return None, error

        name = kwargs["name"]
        cluster = kwargs.get("cluster", 'g')

        f = sftp.open("chemtools/%s.gjf" % name, 'w')
        f.write(gjfstring)
        f.close()


        if jobstring is None:
            jobstring = write_job(internal=True, **kwargs)
        f2 = sftp.open("chemtools/%s.%sjob" % (name, cluster), 'w')
        f2.write(jobstring)
        f2.close()

        s = "qsub chemtools/%s.%sjob" % (name, cluster)
        _, stdout, stderr = ssh.exec_command(s)
        stderr = stderr.readlines()
        if stderr:
            return None, stderr[0]

        jobid = stdout.readlines()[0].split(".")[0]
    except Exception as e:
        return None, str(e)
    return jobid, None

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
                print temp[1]
                results["failed"].append((name, temp[1]))
    return results

def run_standard_job(credential, molecule, **kwargs):
    results = {"jobid": None, "error": None, "cluster": credential.cluster.name}
    try:
        out = gjfwriter.GJFWriter(molecule, kwargs.get("keywords", "b3lyp/6-31g(d)"))
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
            out = gjfwriter.GJFWriter(mol, kwargs.get("keywords", "b3lyp/6-31g(d)"))
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

def _get_columns(lines):
    toprow = [x.strip() for x in lines[2].strip().split() if x]

    bottomrow = [x.strip() for x in lines[3].strip().split() if x]
    bottomrow.remove("Job")
    idx = bottomrow.index("ID")
    bottomrow[idx] = "Job "+bottomrow[idx]

    timeidx = bottomrow.index("Time")
    timeidx2 = bottomrow.index("Time", timeidx+1)
    memidx = bottomrow.index("Memory")
    idxes = [timeidx,timeidx2,memidx]
    order = sorted(idxes)
    argorder = [order.index(x) for x in idxes]

    for i, x in enumerate(idxes):
        bottomrow[x] = ' '.join([toprow[argorder[i]], bottomrow[x]])
    return bottomrow

def _get_jobs(cred, i, results):
    wantedcols = ["Job ID", "Username", "Jobname", "Req'd Memory", "Req'd Time", 'Elap Time', 'S']
    try:
        ssh = cred.get_ssh_connection()

        with ssh:
            _, stdout, stderr = ssh.exec_command("qstat -u %s" % cred.username)
            stderr.readlines()  # seems to need this slight delay to display the jobs

            jobs = []
            lines = stdout.readlines()

            cols = _get_columns(lines[:5])
            colsidx = []
            for x in wantedcols:
                try:
                    colsidx.append(cols.index(x))
                except IndexError:
                    pass

            for job in lines[5:]:
                t = job.split()
                temp = []
                for idx in colsidx:
                    temp.append(t[idx])
                temp[0] = temp[0].split('.')[0]
                jobs.append(temp)
        results[i] = {"name": cred.cluster.name, "columns": wantedcols, "jobs": jobs}
    except Exception as e:
        print e
        results[i] = {"name": cred.cluster.name, "columns": wantedcols, "jobs": []}

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

def wait_for_compression(ssh, zippath):
    done = False
    while not done:
        _, stdout, _ = ssh.exec_command("ls -lah %s" % zippath)
        # check that the size is not 0
        if stdout.readlines()[0].split()[4] != "0":
            done = True
        else:
            time.sleep(.01)

def get_compressed_file(ssh, sftp, path):
    dirname, fname = os.path.split(path)
    fbakpath = path + ".bak"

    ext = int(time.time())
    zipname = "temp%s.bz2" % ext
    zippath = os.path.join(dirname, zipname)

    s = "bzip2 -c < {0} > {1}; cp {0} {2}".format(path, zippath, fbakpath)
    _, _, err = ssh.exec_command(s)
    err = err.readlines()

    if err:
        s = "rm {0}; mv {1} {2}".format(zippath, fbakpath, path)
        ssh.exec_command(s)
        return None, err, None

    wait_for_compression(ssh, zippath)

    decompresser = bz2.BZ2Decompressor()
    ftemp = sftp.open(zippath, "rb").read()
    return StringIO(decompresser.decompress(ftemp)), None, zippath

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
