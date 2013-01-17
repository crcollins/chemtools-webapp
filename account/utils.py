from Crypto.PublicKey import RSA
from Crypto import Random

from chem.utils import get_ssh_connection, StringIO


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

def update_all_ssh_keys(username, old_private, new_public):
    for server in ["gordon.sdsc.edu"]:
        with get_ssh_connection(server, username, StringIO(old_private)) as ssh:
            s = """
            cp ~/.ssh/authorized_keys ~/.ssh/authorized_keys.bak;
            { sed -e '/chemtools-webapp/d' ~/.ssh/authorized_keys.bak && echo "%s"; } > ~/.ssh/authorized_keys;
            rm ~/.ssh/authorized_keys.bak
            """ % new_public
            ssh.exec_command(s)
