import os

from django.template import loader, Context
from django.shortcuts import render
import paramiko

import gjfwriter

def write_job(**kwargs):
    if "cluster" in kwargs and kwargs["cluster"] in "bcgbht":
        template = "chem/jobs/%sjob.txt" % kwargs["cluster"]
        c = Context({
            "name" : kwargs["name"],
            "email": kwargs["email"],
            "nodes": kwargs["nodes"],
            "ncpus": int(kwargs["nodes"]) * 16,
            "time" : "%s:00:00" % kwargs["time"],
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
        jobs = [int(x.split(".")[0]) for x in lines]
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

    _, stdout, _ = ssh.exec_command(". ~/.bash_profile; qstat -u ccollins")
    ssh.close()
    return stdout.readlines()[5:]

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
