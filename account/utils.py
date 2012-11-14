from Crypto.PublicKey import RSA
from Crypto import Random

def generate_key_pair(username=None):
    random_generator = Random.new().read
    key = RSA.generate(2048, random_generator)
    if username is None:
        end = "chemtools-webapp"
    else:
        end = username + "@chemtools-webapp"
    a = {
        "public"  : " ".join([key.publickey().exportKey("OpenSSH"), end]),
        "private" : key.exportKey('PEM'),
    }
    return a