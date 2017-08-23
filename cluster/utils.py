import threading
import logging
from collections import defaultdict

from project.utils import SSHClient, SFTPClient

from models import Credential, Job
from data.models import JobTemplate


logger = logging.getLogger(__name__)


WANTED_COLS = ["Job ID", "Username", "Jobname", "Req'd Memory", "Req'd Time",
               "Elap Time", "S"]


def get_ssh_connection_obj(obj):
    if isinstance(obj, Credential):
        try:
            return obj.get_ssh_connection()
        except:  # sometimes this times out
            return obj.get_ssh_connection()
    elif isinstance(obj, SSHClient):
        return obj
    else:
        logger.warn("The object passed to get an SSH connection was not of the correct type")
        raise TypeError


def get_sftp_connection_obj(obj):
    if isinstance(obj, Credential):
        try:
            return obj.get_sftp_connection()
        except:  # sometimes this times out
            return obj.get_sftp_connection()
    elif isinstance(obj, SFTPClient):
        return obj
    else:
        logger.warn("The object passed to get an SFTP connection was not of the correct type")
        raise TypeError


def get_credentials_from_request(request):
    creds = []
    usercreds = request.user.credentials.all()
    for key in request.POST:
        if set(key).intersection("@:-") and request.POST[key] == "on":
            username, hostname = key.split('@')
            hostname, port = hostname.split(':')
            port, id_ = port.split('-')
            try:
                cred = usercreds.get(
                    id=id_,
                    username=username,
                    cluster__hostname=hostname,
                    cluster__port=int(port))
                creds.append(cred)
            except Exception:
                logger.info("Could not find the credential: %s@%s:%s" % (username, hostname, port))
                pass
    return creds


def get_clusters_from_request(request):
    clusters = []
    userclusters = request.user.clusters.all()
    for key in request.POST:
        if ':' in key and request.POST[key] == "on":
            try:
                creator, hostname, port, id_ =  key.split(':')
                cluster = userclusters.get(
                    id=id_,
                    creator__username=creator,
                    hostname=hostname,
                    port=port)
                clusters.append(cluster)
            except Exception as e:
                logger.info("Could not find the cluster: %s:%s:%s:%s" % (creator, hostname, port, id_))
                pass
    return clusters


def _make_folders(ssh):
    folder = 'chemtools/done/'
    _, _, stderr = ssh.exec_command("mkdir -p %s" % folder)
    err = stderr.readlines()
    if err:
        return err[0]
    return None


def add_fileparser(ssh, sftp):
    command = "ls chemtools/fileparser.py"
    _, stdout, stderr = ssh.exec_command(command)
    if stderr.read():
        with sftp.open("chemtools/fileparser.py", 'w') as f:
            with open("chemtools/fileparser.py", 'r') as f2:
                f.write(f2.read())

    command = "python chemtools/fileparser.py -"
    _, stdout, stderr = ssh.exec_command(command)

    err = stderr.read()
    if "No module named argparse" in err:
        import argparse
        with sftp.open("chemtools/argparse.py", 'w') as f:
            with open(argparse.__file__.rstrip('c'), 'r') as f2:
                f.write(f2.read())
        _, stdout, stderr = ssh.exec_command(command)
        err = stderr.read()
        if err:
            logger.warn("Could not add the fileparser: %s" % err)
            return err
    return None


def _run_job(ssh, sftp, gjfstring, jobstring=None, **kwargs):
    try:
        error = _make_folders(ssh)
        if error:
            return None, "folder - " + error

        name = kwargs.get("name", "chemtoolsjob")
        gjfname = "chemtools/%s.gjf" % name
        jobname = "chemtools/%s.job" % name

        f = sftp.open(gjfname, 'w')
        f.write(gjfstring)
        f.close()

        if jobstring is None:
            jobstring = JobTemplate.render(internal=True, **kwargs)
        f2 = sftp.open(jobname, 'w')
        f2.write(jobstring)
        f2.close()

        # TODO: Make this safer
        s = "cd chemtools; qsub " + "%s.job" % name
        _, stdout, stderr = ssh.exec_command(s)
        stderr = stderr.readlines()
        if stderr:
            return None, "qsub - " + stderr[0]

        jobid = stdout.readlines()[0].split(".")[0]
    except Exception as e:
        logger.warn("Could not run the job: %s" % e)
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


def _get_jobs(cred, cluster, i, results):
    try:
        ssh = cred.get_ssh_connection()

        with ssh:
            # TODO: Make this safer
            _, stdout, stderr = ssh.exec_command("qstat -u %s" % cred.username)
            # seems to need this slight delay to display the jobs
            stderr.readlines()

            jobs = []
            lines = stdout.readlines()

            cols = _get_columns(lines[:5])
            colsidx = []
            for x in WANTED_COLS:
                try:
                    colsidx.append(cols.index(x))
                except IndexError:
                    pass

            for job in lines[5:]:
                t = job.split()
                # empty line implies a split in the table
                # this is seen on blacklight with the "Total cpus requested
                # from running jobs" line at the end.
                if t == []:
                    break

                temp = []
                for idx in colsidx:
                    temp.append(t[idx])
                temp[0] = temp[0].split('.')[0]
                jobs.append(temp)
        results[i] = {"name": cluster, "columns": WANTED_COLS, "jobs": jobs}
    except Exception:
        logger.info("No jobs running for %s", cred)
        results[i] = {"name": cluster, "columns": WANTED_COLS, "jobs": []}


def get_jobs(credentials):
    threads = []
    # results is a mutable object, so as the threads complete they save their
    # results into this object. This method is used in lieu of messing with
    # multiple processes
    results = [None] * len(credentials)
    for i, cred in enumerate(credentials):
        t = threading.Thread(target=_get_jobs,
                             args=(cred, cred.cluster.name, i, results))
        t.start()
        threads.append(t)

    for t in threads:
        t.join(20)

    clusters = [x for x in results if x]
    for cred, cluster in zip(credentials, clusters):
        jobs = defaultdict(list)
        jobids = []
        for job in cluster["jobs"]:
            status = job[-1]
            job_id = job[0]
            jobids.append(job_id)
            if not Job.objects.filter(jobid=job_id, credential=cred):
                continue  # outside submited jobs not allowed
            jobs[status].append(job_id)
        running = Job.get_running_jobs(credential=cred)
        unknown = running.exclude(
            jobid__in=set(jobids)).values_list('jobid', flat=True)
        if unknown:
            jobs[Job.UNKNOWN] = list(unknown)
        Job.update_states(cred, jobs)
    return clusters
