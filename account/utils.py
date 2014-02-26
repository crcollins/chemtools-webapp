import random
import hashlib
import functools

from Crypto.PublicKey import RSA
from Crypto import Random

from project.utils import StringIO, get_ssh_connection
from cluster.models import Credential


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
    for cred in Credential.objects.filter(user=user, use_password=False):
        with cred.get_ssh_connection() as ssh:
            s = "cp ~/.ssh/authorized_keys ~/.ssh/authorized_keys.bak"
            _, _, err = ssh.exec_command(s)
            a = err.readlines()
            if a:
                raise Exception(str(a))

            # _ is used because ssh keys can have / in them
            s1 = "sed ~/.ssh/authorized_keys.bak -e 's_ssh-rsa "
            s2 = ".* %s@chemtools-webapp_%s_' > ~/.ssh/authorized_keys"
            _, _, err = ssh.exec_command(s1 + s2 % (user.username, new_public))
            a = err.readlines()
            if a:
                raise Exception(str(a))


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
