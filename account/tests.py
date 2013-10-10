from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from Crypto.PublicKey import RSA

import views
import utils

def _register(client, data):
    response = client.post(reverse(views.register_user), data)
    assert response.status_code == 200
    content = response.content
    start = content.index("Please click")
    end = content.index("this", start)-2
    key = content[start:end].split('href="')[1]
    response = client.get(reverse(views.activate_user, args=(key, )))
    assert response.status_code == 200
    v = client.login(username=data["username"], password=data["new_password1"])
    assert v
    client.logout()

class RegistrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_page(self):
        response = self.client.get(reverse(views.register_user))
        self.assertEqual(response.status_code, 200)

    def test_register(self):
        data = {
            "username": "testman",
            "email": "testman@test.com",
            "new_password1": "mypass",
            "new_password2": "mypass",
        }
        _register(self.client, data)

    def test_register_taken_username(self):
        data = {
            "username": "testman1",
            "email": "testman1@test.com",
            "new_password1": "mypass",
            "new_password2": "mypass",
        }
        _register(self.client, data)
        try:
            _register(self.client, data)
            raise Exception()
        except ValueError:
            pass

    def test_register_bad_password(self):
        data = {
            "username": "testman",
            "email": "testman@test.com",
            "new_password1": "mypass",
            "new_password2": "mypass123",
        }
        try:
            _register(self.client, data)
            raise Exception()
        except ValueError:
            pass


class UtilsTestCase(TestCase):
    def test_generate_key_pair(self):
        self.assertIsNotNone(utils.generate_key_pair())
        self.assertIsNotNone(utils.generate_key_pair("username"))

    def test_key_pair(self):
        keypair = utils.generate_key_pair()

        key = RSA.importKey(keypair["private"])
        pubkey = RSA.importKey(keypair["public"])

        message = "The quick brown fox jumps over the lazy dog."
        sig = key.sign(message, '')
        self.assertTrue(pubkey.verify(message, sig))

    def test_invalid_key_pair(self):
        keypair = utils.generate_key_pair()
        keypair["private"] = keypair["private"][:50]+keypair["private"][53:]
        keypair["public"] = keypair["public"][:50]+keypair["public"][53:]
        try:
            key = RSA.importKey(keypair["private"])
            pubkey = RSA.importKey(keypair["public"])
        except:
            return
        raise Exception

    def test_mismatch_keypair(self):
        keypair0 = utils.generate_key_pair()
        keypair1 = utils.generate_key_pair()

        key = RSA.importKey(keypair0["private"])
        pubkey = RSA.importKey(keypair1["public"])

        message = "The quick brown fox jumps over the lazy dog."
        sig = key.sign(message, '')
        self.assertFalse(pubkey.verify(message, sig))

    def test_generate_key(self):
        self.assertIsNotNone(utils.generate_key("some string"))