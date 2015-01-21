import random
import hashlib
import logging

from Crypto.PublicKey import RSA
from Crypto import Random


logger = logging.getLogger(__name__)


def generate_key_pair(username=None):
    random_generator = Random.new().read
    key = RSA.generate(2048, random_generator)
    if username is None:
        end = "chemtools-webapp"
    else:
        end = username + "@chemtools-webapp"
    a = {
        "public": " ".join([key.publickey().exportKey("OpenSSH"), end]),
        "private": key.exportKey('PEM'),
    }
    return a


def update_all_ssh_keys(user, new_public):
    for cred in user.credentials.filter(use_password=False):
        with cred.get_ssh_connection() as ssh, cred.get_sftp_connection() as sftp:
            s = "cp ~/.ssh/authorized_keys ~/.ssh/authorized_keys.bak"
            _, _, err = ssh.exec_command(s)
            a = err.readlines()
            if a:
                logger.warn("Unable to update ssh key: %s - %s" % (cred, a))
                raise Exception(str(a))

            _, out, err = ssh.exec_command('echo $HOME')
            base = out.read().strip()

            with sftp.open("%s/.ssh/authorized_keys.bak" % base, 'r') as f1:
                with sftp.open("%s/.ssh/authorized_keys" % base, 'w') as f2:
                    for line in f1:
                        if "chemtools-webapp" in line:
                            line = new_public
                        f2.write(line)


def generate_key(text):
    salt = hashlib.sha1(str(random.random())).hexdigest()[:10]
    return hashlib.sha1(salt + text).hexdigest()


class Pages(object):

    def __init__(self):
        self.__registry = dict()

    def __getitem__(self, name):
        return self.__registry[name]

    def __setitem__(self, name, value):
        self.__registry[name] = value

    def __iter__(self):
        return iter(sorted(self.__registry.keys()))


PAGES = Pages()


def add_account_page(url):
    def decorator(f):
        PAGES[url] = f
        return f
    return decorator
