import os
import bz2
from cStringIO import StringIO
import time

from django.template import loader, Context
from django.shortcuts import render
import paramiko

import gjfwriter
import fileparser

def write_job(**kwargs):
    for x in kwargs:
        kwargs[x] = kwargs[x][0]

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

def start_run_molecule(molecule, **kwargs):
    try:
        out = gjfwriter.Output(molecule, kwargs["basis"])
    except Exception as e:
        return None, e

    with open(os.path.expanduser("~/.ssh/id_rsa"), 'r') as pkey:
        sftp = get_sftp_connection("gordon.sdsc.edu", "ccollins", pkey)
        pkey.seek(0) # reset to start of key file
        ssh = get_ssh_connection("gordon.sdsc.edu", "ccollins", pkey)

    for folder in ["test/", "done/"]:
        _, _, testerr = ssh.exec_command("ls %s" % folder)
        if testerr.readlines():
            _, _, testerr2 = ssh.exec_command("mkdir %s" % folder)
            testerr2 = testerr2.readlines()
            if testerr2:
                ssh.close()
                sftp.close()
                return None, testerr2[0]

    if "name" in kwargs:
        name = kwargs["name"]
    else:
        name = molecule

    f = sftp.open("test/%s.gjf" % name, 'w')
    f.write(out.write_file())
    f.close()

    f2 = sftp.open("test/%s.gjob" % name, 'w')
    kwargs["cluster"] = "g"
    f2.write(write_job(**kwargs))
    f2.close()
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command(". ~/.bash_profile; qsub test/%s.gjob" % name)
    stderr = stderr.readlines()
    if stderr:
        ssh.close()
        return None, stderr[0]
    try:
        jobid = int(stdout.readlines()[0].split(".")[0])
    except Exception as e:
        return None, e

    return jobid, None

def kill_run_job(jobid):
    with open(os.path.expanduser("~/.ssh/id_rsa"), 'r') as pkey:
        ssh = get_ssh_connection("gordon.sdsc.edu", "ccollins", pkey)

    a = get_all_jobs()
    if a:
        jobs = [x[0] for x in a]
    else:
        ssh.close()
        return "There are no jobs running."

    if jobid in jobs:
        _, _, stderr = ssh.exec_command(". ~/.bash_profile; qdel %d" % jobid)
        ssh.close()
    else:
        ssh.close()
        return "That job number is not running."

    b = stderr.readlines()
    if b:
        return b

def get_all_jobs():
    with open(os.path.expanduser("~/.ssh/id_rsa"), 'r') as pkey:
        ssh = get_ssh_connection("gordon.sdsc.edu", "ccollins", pkey)

    _, stdout, stderr = ssh.exec_command(". ~/.bash_profile; qstat -u ccollins")
    stderr.readlines() # seems to need this slight delay to display the jobs
    ssh.close()

    jobs = []
    for job in stdout.readlines()[5:]:
        t = job.split()
        temp = t[0].split('.') + t[3:4] + t[5:7] + t[8:]
        jobs.append(temp)
    return jobs

def recover_output(name):
    with open(os.path.expanduser("~/.ssh/id_rsa"), 'r') as pkey:
        sftp = get_sftp_connection("gordon.sdsc.edu", "ccollins", pkey)
        pkey.seek(0) # reset to start of key file
        ssh = get_ssh_connection("gordon.sdsc.edu", "ccollins", pkey)

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
        sftp = get_sftp_connection("gordon.sdsc.edu", "ccollins", pkey)
        pkey.seek(0) # reset to start of key file
        ssh = get_ssh_connection("gordon.sdsc.edu", "ccollins", pkey)

    _, stdout, stderr = ssh.exec_command("ls test/%s.*" % name)
    files = [x.replace("\n", "").lstrip("test/") for x in stdout.readlines()]
    err = stderr.readlines()

    if err:
        return err
    for fname in files:
        if name+".log" == fname: # only download log files for now
            ext = int(time.time())
            s = "bzip2 -c < test/{0} > test/temp{1}.bz2; mv test/{0} test/{0}.bak".format(fname, ext)
            ssh.exec_command(s)

            # wait until comression on cluster is done
            done = False
            while not done:
                _, stdout, _ = ssh.exec_command("ls -lah test/temp%d.bz2" % ext)
                # check that the size is not 0
                if stdout.readlines()[0].split()[4] != "0":
                    done = True
                else:
                    time.sleep(.01)

            decompresser = bz2.BZ2Decompressor()
            ftemp = sftp.open("test/temp%d.bz2" % ext, "rb").read()

            f = StringIO(decompresser.decompress(ftemp))
            parser = fileparser.LogReset(f, fname)
            f.close()

            f2 = sftp.open("test/%s" % fname, "w")
            f2.write(parser.format_output(errors=False))
            f2.close()
            ssh.exec_command("rm test/temp%d.bz2" % ext)

    sftp.close()
    ssh.close()

def get_sftp_connection(hostname, username, key, port=22):
    pkey = paramiko.RSAKey.from_private_key(key)

    transport = paramiko.Transport((hostname, port))
    transport.connect(username=username, pkey=pkey)
    return paramiko.SFTPClient.from_transport(transport)

def get_ssh_connection(hostname, username, key, port=22):
    pkey = paramiko.RSAKey.from_private_key(key)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, pkey=pkey)
    return client
