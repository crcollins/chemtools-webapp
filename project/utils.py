import cStringIO

import paramiko

class StringIO(object):
    def __init__(self, *args, **kwargs):
        self.s = cStringIO.StringIO(*args, **kwargs)
        self.name = kwargs.get("name", "")
    def __getattr__(self, key):
        return getattr(self.s, key)
    def __iter__(self):
        for line in self.readlines():
            yield line
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        self.close()

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