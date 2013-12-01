import os
import bz2
import time

from chemtools.utils import write_job
from project.utils import StringIO, SSHClient, SFTPClient

from models import Credential


def get_ssh_connection(obj):
    if isinstance(obj, Credential):
        try:
            return obj.get_ssh_connection()
        except:  # sometimes this timesout
            return obj.get_ssh_connection()
    elif isinstance(obj, SSHClient):
        return obj
    else:
        raise TypeError


def get_sftp_connection(obj):
    if isinstance(obj, Credential):
        try:
            return obj.get_sftp_connection()
        except:  # sometimes this timesout
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
            return None, "folder - " + error

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
            return None, "qsub - " + stderr[0]

        jobid = stdout.readlines()[0].split(".")[0]
    except Exception as e:
        return None, str(e)
    return jobid, None


def _get_columns(lines):
    toprow = [x.strip() for x in lines[2].strip().split() if x]

    bottomrow = [x.strip() for x in lines[3].strip().split() if x]
    bottomrow.remove("Job")
    idx = bottomrow.index("ID")
    bottomrow[idx] = "Job " + bottomrow[idx]

    timeidx = bottomrow.index("Time")
    timeidx2 = bottomrow.index("Time", timeidx + 1)
    memidx = bottomrow.index("Memory")
    idxes = [timeidx, timeidx2, memidx]
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
                # empty line implies a split in the table
                # this is seen on blacklight with the "Total cpus requested from running jobs" line at the end.
                if t == []:
                    break

                temp = []
                for idx in colsidx:
                    temp.append(t[idx])
                temp[0] = temp[0].split('.')[0]
                jobs.append(temp)
        results[i] = {"name": cred.cluster.name, "columns": wantedcols, "jobs": jobs}
    except Exception as e:
        print e
        results[i] = {"name": cred.cluster.name, "columns": wantedcols, "jobs": []}


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
