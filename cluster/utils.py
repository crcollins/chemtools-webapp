import os
import bz2
import zipfile
import tarfile
import time
import re

import paramiko

from chemtools import gjfwriter
from chemtools import fileparser
from chemtools.utils import name_expansion
from project.utils import get_ssh_connection, get_sftp_connection, StringIO

from models import Credential

PRE_INFO = ". ~/.bash_profile; source .login; "

def get_connections(server, user):
    try:
        profile = user.get_profile()
    except AttributeError:
        profile = None
    if profile and profile.xsede_username and profile.private_key:
        username = profile.xsede_username
        key = StringIO(profile.private_key)
    else:
        username = "ccollins"
        key = open(os.path.expanduser("~/.ssh/id_rsa"), 'r')
    sftp = get_sftp_connection(server, username, key=key)
    key.seek(0)  # reset to start of key file
    ssh = get_ssh_connection(server, username, key=key)
    return ssh, sftp

def make_folders(ssh):
    for folder in ["chemtools/", "chemtools/done/"]:
        _, _, testerr = ssh.exec_command("ls %s" % folder)
        if testerr.readlines():
            _, _, testerr2 = ssh.exec_command("mkdir %s" % folder)
            testerr2 = testerr2.readlines()
            if testerr2:
                return testerr2[0]
    return None

import random
def run_job(user, gjfstring, jobstring=None, **kwargs):
    if random.random() > .5:
        jobid = None
        e = "There was an error"
    else:
        jobid = random.randint(0, 10000)
        e = None
    return jobid, e

    ssh, sftp = get_connections("gordon.sdsc.edu", user)
    with ssh, sftp:
        error = make_folders(ssh)
        if error:
            return None, error

        name = kwargs["name"]
        custer = kwargs.get("cluster", 'g')

        f = sftp.open("chemtools/%s.gjf" % name, 'w')
        f.write(gjfstring)
        f.close()


        if jobstring is None:
            jobstring = write_job(internal=True, **kwargs)
        f2 = sftp.open("chemtools/%s.%sjob" % (name, cluster))
        f2.write(jobstring)
        f2.close()

        s = PRE_INFO + "qsub chemtools/%s.%sjob" % (name, cluster)
        _, stdout, stderr = ssh.exec_command(s)
        stderr = stderr.readlines()
        if stderr:
            return None, stderr[0]
        try:
            jobid = stdout.readlines()[0].split(".")[0]
        except Exception as e:
            return None, e
        return jobid, None

def run_standard_job(user, molecule, **kwargs):
    results = {"jobid": None, "error": None}

    if not user.is_staff:
        results["error"] = "You must be a staff user to submit a job."
        return results
    try:
        out = gjfwriter.GJFWriter(molecule, kwargs.get("keywords", "b3lyp/6-31g(d)"))
    except Exception as e:
        results["error"] = str(e)
        return results

    gjf = out.get_gjf()
    name = kwargs.get("name", molecule)
    jobid, error = run_job(user, gjf, **kwargs)
    results["jobid"] = jobid
    results["error"] = error
    # if error is None:
    #     dnew.pop("template")
    #     job = Job(molecule=molecule, jobid=jobid, **dnew)
    #     job.save()
    return results

def run_standard_jobs(user, string, **kwargs):
    results = {
        "worked": [],
        "failed": [],
        "error": None,
    }

    if not user.is_staff:
        results["error"] = "You must be a staff user to submit a job."
        return results

    for mol in name_expansion(string):
        dnew = kwargs.copy()
        dnew["name"] = re.sub(r"{{\s*name\s*}}", mol, dnew["name"])
        a = run_standard_job(user, mol, **dnew)

        if a["error"] is None:
            results["worked"].append((mol, a["jobid"]))
        else:
            results["failed"].append((mol, a["error"])) # str is a hack if real errors bubble up
    return results

def kill_job(user, jobid):
    ssh, _ = get_connections("gordon.sdsc.edu", user)

    with ssh:
        a = get_all_jobs(user)
        if a:
            jobs = [x[0] for x in a]
        else:
            return "There are no jobs running."

        if jobid in jobs:
            _, _, stderr = ssh.exec_command(PRE_INFO + "qdel %s" % jobid)
        else:
            return "That job number is not running."

        b = stderr.readlines()
        if b:
            return b

def get_all_jobs(user):
    full_jobs = []
    for cred in user.credentials.all():
        try:
            ssh = cred.get_ssh_connection()

            with ssh:
                _, stdout, stderr = ssh.exec_command(PRE_INFO + "qstat -u %s" % cred.username)
                print stderr.readlines()  # seems to need this slight delay to display the jobs

                jobs = []
                for job in stdout.readlines()[5:]:
                    t = job.split()
                    temp = [t[0].split('.')[0]] + [cred.cluster.name] + t[3:4] + t[5:7] + t[8:]
                    jobs.append(temp)
                full_jobs.extend(jobs)
        except Exception as e:
            print e
            pass
    return full_jobs

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
    ssh, sftp = get_connections("gordon.sdsc.edu", user)

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
    ssh, sftp = get_connections("gordon.sdsc.edu", user)

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