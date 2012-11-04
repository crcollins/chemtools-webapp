import os
import bz2
import cStringIO
import time

from django.template import loader, Context
import paramiko

import gjfwriter
import fileparser

def write_job(**kwargs):
    if "cluster" in kwargs and kwargs["cluster"] in "bcgbht":
        template = "chem/jobs/%sjob.txt" % kwargs["cluster"]
        c = Context({
            "name" : kwargs["name"],
            "email": kwargs["email"],
            "nodes": kwargs["nodes"],
            "ncpus": int(kwargs["nodes"]) * 16,
            "time" : "%s:00:00" % kwargs["walltime"],
            })
        return loader.render_to_string(template, c)
    else:
        return ''

###########################################################
#  SSH stuff
###########################################################

class SSHClient(paramiko.SSHClient):
    def __init__(self, *args, **kwargs):
        super(SSHClient, self).__init__(*args, **kwargs)
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        self.close()

class SFTPClient(paramiko.SFTPClient):
    def __init__(self, *args, **kwargs):
        super(SFTPClient, self).__init__(*args, **kwargs)
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        self.close()

class StringIO(object):
    def __init__(self, *args, **kwargs):
        self.s = cStringIO.StringIO(*args, **kwargs)
    def __getattr__(self, key):
        return getattr(self.s, key)
    def __iter__(self):
        for line in self.readlines():
            yield line
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        self.close()

def get_sftp_connection(hostname, username, key, port=22):
    pkey = paramiko.RSAKey.from_private_key(key)

    transport = paramiko.Transport((hostname, port))
    transport.connect(username=username, pkey=pkey)
    return SFTPClient.from_transport(transport)

def get_ssh_connection(hostname, username, key, port=22):
    pkey = paramiko.RSAKey.from_private_key(key)

    client = SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, pkey=pkey)
    return client

def get_connections(server, username, pkey):
    sftp = get_sftp_connection(server, username, pkey)
    pkey.seek(0) # reset to start of key file
    ssh = get_ssh_connection(server, username, pkey)
    return ssh, sftp

def make_folders(ssh):
    for folder in ["test/", "done/"]:
        _, _, testerr = ssh.exec_command("ls %s" % folder)
        if testerr.readlines():
            _, _, testerr2 = ssh.exec_command("mkdir %s" % folder)
            testerr2 = testerr2.readlines()
            if testerr2:
                return testerr2[0]
    return None

def start_run_molecule(molecule, **kwargs):
    try:
        out = gjfwriter.Output(molecule, kwargs["basis"])
    except Exception as e:
        return None, e

    with open(os.path.expanduser("~/.ssh/id_rsa"), 'r') as pkey:
        ssh, sftp = get_connections("gordon.sdsc.edu", "ccollins", pkey)

    with ssh, sftp:
        error = make_folders(ssh)
        if error:
            return None, error

        name = kwargs.get("name", molecule)

        f = sftp.open("test/%s.gjf" % name, 'w')
        f.write(out.write_file())
        f.close()

        f2 = sftp.open("test/%s.gjob" % name, 'w')
        kwargs["cluster"] = "g"
        f2.write(write_job(**kwargs))
        f2.close()

        s = ". ~/.bash_profile; qsub test/%s.gjob" % name
        _, stdout, stderr = ssh.exec_command(s)
        stderr = stderr.readlines()
        if stderr:
            return None, stderr[0]
        try:
            jobid = int(stdout.readlines()[0].split(".")[0])
        except Exception as e:
            return None, e

        return jobid, None

def kill_job(jobid):
    with open(os.path.expanduser("~/.ssh/id_rsa"), 'r') as pkey:
        ssh = get_ssh_connection("gordon.sdsc.edu", "ccollins", pkey)

    with ssh:
        a = get_all_jobs()
        if a:
            jobs = [x[0] for x in a]
        else:
            return "There are no jobs running."

        if jobid in jobs:
            _, _, stderr = ssh.exec_command(". ~/.bash_profile; qdel %s" % jobid)
        else:
            return "That job number is not running."

        b = stderr.readlines()
        if b:
            return b

def get_all_jobs():
    with open(os.path.expanduser("~/.ssh/id_rsa"), 'r') as pkey:
        ssh = get_ssh_connection("gordon.sdsc.edu", "ccollins", pkey)

    with ssh:
        _, stdout, stderr = ssh.exec_command(". ~/.bash_profile; qstat -u ccollins")
        stderr.readlines() # seems to need this slight delay to display the jobs

    jobs = []
    for job in stdout.readlines()[5:]:
        t = job.split()
        temp = t[0].split('.') + t[3:4] + t[5:7] + t[8:]
        jobs.append(temp)
    return jobs

def wait_for_compression(ssh, zippath):
    done = False
    while not done:
        _, stdout, _ = ssh.exec_command("ls -lah %s" % zippath)
        # check that the size is not 0
        if stdout.readlines()[0].split()[4] != "0":
            done = True
        else:
            time.sleep(.01)

def recover_output(name):
    with open(os.path.expanduser("~/.ssh/id_rsa"), 'r') as pkey:
        ssh, sftp = get_connections("gordon.sdsc.edu", "ccollins", pkey)

    _, stdout, stderr = ssh.exec_command("ls done/%s.*" % name)
    files = [x.replace("\n", "").lstrip("done/") for x in stdout.readlines()]
    err = stderr.readlines()

    if err:
        return err
    for fname in files:
        if ".log" in fname: # only download log files for now
            f = sftp.open("done/"+fname, "r")
            f2 = open(fname, "w")
            for line in f:
                f2.write(line)
            f.close()
            f2.close()
    sftp.close()
    ssh.close()

def reset_output(name):
    with open(os.path.expanduser("~/.ssh/id_rsa"), 'r') as pkey:
        ssh, sftp = get_connections("gordon.sdsc.edu", "ccollins", pkey)

    _, stdout, stderr = ssh.exec_command("ls test/%s.*" % name)
    files = [x.replace("\n", "").lstrip("test/") for x in stdout.readlines()]
    err = stderr.readlines()

    if err:
        sftp.close()
        ssh.close()
        return None, err
    for fname in files:
        if name+".log" == fname: # only download log files for now
            ext = int(time.time())
            s = "bzip2 -c < test/{0} > test/temp{1}.bz2; mv test/{0} test/{0}.bak".format(fname, ext)
            ssh.exec_command(s)

            # wait until comression on cluster is done
            wait_for_compression(ssh, "test/temp%d.bz2" % ext)

            decompresser = bz2.BZ2Decompressor()
            ftemp = sftp.open("test/temp%d.bz2" % ext, "rb").read()

            f = StringIO(decompresser.decompress(ftemp))
            parser = fileparser.LogReset(f, fname)
            f.close()

            f2 = sftp.open("test/%s" % fname, "w")
            f2.write(parser.format_output(errors=False))
            f2.close()
            ssh.exec_command("rm test/temp%d.bz2" % ext)
            _, stdout, stderr = ssh.exec_command("qsub test/%s.gjob" % fname)
    err = stderr.readlines()
    if err:
        sftp.close()
        ssh.close()
        return None, err

    e = None
    try:
        jobid = stdout.readlines()[0].split('.')[0]
    except Exception as e:
        jobid = None
    sftp.close()
    ssh.close()
    return jobid, e