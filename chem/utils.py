import os

from django.template import loader, Context
from django.shortcuts import render
import paramiko

import gjfwriter

def write_job(**kwargs):
    if "cluster" in kwargs:
        template = "chem/jobs/%sjob.txt" % kwargs["cluster"]
        t = loader.get_template(template)
        c = Context(kwargs)
        return t.render(c)
    else:
        return ''


def start_run_molecule(molecule, **kwargs):
    try:
        out = gjfwriter.Output(molecule, kwargs["basis"])
    except Exception as e:
        return e
    with open(os.path.expanduser("~/.ssh/id_rsa"), 'r') as pkey:
        sftp = get_sftp_connection("gordon.sdsc.edu", "ccollins", pkey)
        f = sftp.open("test/%s.gjf" % molecule, 'w')
        f.write(out.write_file())
        f.close()
        f = sftp.open("test/%s.gjob" % molecule, 'w')
        kwargs["cluster"] = "g"
        a = write_job(**kwargs)
        f.write(a)
        f.close()
        sftp.close()


        pkey.seek(0)
        ssh = get_ssh_connection("gordon.sdsc.edu", "ccollins", pkey)
        stdin, stdout, stderr = ssh.exec_command(". ~/.bash_profile; ls test/")
        ssh.close()
        print "close ssh"


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
