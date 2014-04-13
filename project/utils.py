import os
import cStringIO
import base64

from Crypto.Cipher import AES
from Crypto import Random
import paramiko

from settings import AES_KEY


class StringIO(object):
    def __init__(self, *args, **kwargs):
        self.s = cStringIO.StringIO(*args)
        self.name = kwargs.get("name", '')

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
        self.base = ""

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def exec_command(self, command, *args, **kwargs):
        command = self.base + command
        return super(SSHClient, self).exec_command(command, *args, **kwargs)


class SFTPClient(paramiko.SFTPClient):
    def __init__(self, *args, **kwargs):
        super(SFTPClient, self).__init__(*args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()


def get_sftp_connection(hostname, username, key=None, password=None, port=22):
    if key is None and password is None:
        raise Exception("no key or password")

    transport = paramiko.Transport((hostname, port))
    transport.use_compression(compress=True)
    if key:
        pkey = paramiko.RSAKey.from_private_key(key)
        transport.connect(username=username, pkey=pkey)
    else:
        transport.connect(username=username, password=password)
    return SFTPClient.from_transport(transport)


def get_ssh_connection(hostname, username, key=None, password=None, port=22):
    if key is None and password is None:
        raise Exception("no key or password")

    client = SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if key:
        pkey = paramiko.RSAKey.from_private_key(key)
        client.connect(hostname, username=username, pkey=pkey, port=port,
                    allow_agent=False, look_for_keys=False, compress=True)
    else:
        client.connect(hostname, username=username, password=password,
                    port=port, allow_agent=False, look_for_keys=False,
                    compress=True)
    bases = [". ~/.bash_profile; ", "source .login; ", ". ~/.bashrc; "]
    for base in bases:
        _, _, err = client.exec_command(base)
        if not err.readlines():
            client.base = base
            break
    return client


def touch(path, times=None):
    with open(path, 'a'):
        os.utime(path, times)


class AESCipher(object):
    # http://stackoverflow.com/questions/12524994/encrypt-decrypt-using-pycrypto-aes-256
    BS = AES.block_size

    def __init__(self, key=AES_KEY):
        self.key = key

    def _pad(self, s):
        pad = (self.BS - len(s) % self.BS) * chr(self.BS - len(s) % self.BS)
        return s + pad

    def _unpad(self, s):
        return  s[0:-ord(s[-1])]

    def encrypt(self, plain_text):
        raw = self._pad(plain_text)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, cipher_text):
        raw = base64.b64decode(cipher_text)
        iv = raw[:self.BS]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(raw[self.BS:]))
