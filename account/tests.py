from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from Crypto.PublicKey import RSA

import views
import utils


def _register(client, data):
    response = client.post(reverse(views.register_user), data)
    assert response.status_code == 200
    content = response.content
    start = content.index("Please click")
    end = content.index("this", start) - 2
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


class SettingsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.users = [{
            "username": "user1",
            "email": "user1@test.com",
            "new_password1": "mypass",
            "new_password2": "mypass",
        }, {
            "username": "user2",
            "email": "user2@test.com",
            "new_password1": "mypass",
            "new_password2": "mypass",
        }]
        for user in self.users:
            _register(self.client, user)

    def test_get_public_key(self):
        for user in self.users:
            response = self.client.get(reverse(views.get_public_key, args=(user["username"], )))
            self.assertEqual(response.status_code, 200)
            profile = User.objects.get(username=user["username"]).get_profile()
            self.assertEqual(response.content.strip(), profile.public_key)

    def test_change_settings_page(self):
        for user in self.users:
            r = self.client.login(username=user["username"], password=user["new_password1"])
            self.assertTrue(r)
            response = self.client.get(reverse(views.main_settings, args=(user["username"], )))
            self.assertEqual(response.status_code, 200)

    def test_change_settings_redirect(self):
        for i, user in enumerate(self.users):
            r = self.client.login(username=user["username"], password=user["new_password1"])
            self.assertTrue(r)
            opposite = self.users[not i]["username"]
            response = self.client.get(reverse(views.main_settings, args=(opposite, )))
            self.assertEqual(response.status_code, 302)

    def test_change_xsede_username(self):
        for user in self.users:
            r = self.client.login(username=user["username"], password=user["new_password1"])
            self.assertTrue(r)

            response = self.client.get(reverse(views.main_settings, args=(user["username"], )))
            self.assertEqual(response.status_code, 200)

            data = {"xsede_username": user["username"], "email": user["email"]}
            response = self.client.post(reverse(views.main_settings, args=(user["username"], )), data)
            self.assertIn("Settings Successfully Saved", response.content)

            profile = User.objects.get(username=user["username"]).get_profile()
            self.assertEqual(profile.xsede_username, user["username"])

    def test_update_ssh_key(self):
        for user in self.users:
            profile = User.objects.get(username=user["username"]).get_profile()
            r = self.client.login(username=user["username"], password=user["new_password1"])
            self.assertTrue(r)

            response = self.client.get(reverse(views.main_settings, args=(user["username"], )))
            self.assertEqual(response.status_code, 200)

            initial = profile.public_key
            data = {"new_ssh_keypair": "on", "email": user["email"]}
            response = self.client.post(reverse(views.main_settings, args=(user["username"], )), data)
            self.assertIn("Settings Successfully Saved", response.content)

            profile = User.objects.get(username=user["username"]).get_profile()
            self.assertNotEqual(profile.public_key, initial)

    def test_update_password(self):
        for user in self.users:
            r = self.client.login(username=user["username"], password=user["new_password1"])
            self.assertTrue(r)

            response = self.client.get(reverse(views.password_settings, args=(user["username"], )))
            self.assertEqual(response.status_code, 200)
            data = {
                "old_password": user["new_password1"],
                "new_password1": user["new_password1"] + 'a',
                "new_password2": user["new_password2"] + 'a',
                }
            response = self.client.post(reverse(views.password_settings, args=(user["username"], )), data)
            self.assertEqual(response.status_code, 200)
            self.assertIn("Settings Successfully Saved", response.content)
            self.client.logout()

            r = self.client.login(username=user["username"], password=user["new_password1"] + 'a')
            self.assertTrue(r)
            User.objects.get(username=user["username"]).set_password(user["new_password1"])

    def test_add_cluster(self):
        for user in self.users:
            r = self.client.login(username=user["username"], password=user["new_password1"])
            self.assertTrue(r)

            response = self.client.get(reverse(views.cluster_settings, args=(user["username"], )))
            self.assertEqual(response.status_code, 200)
            data = {
                "name": "test-machine",
                "hostname": "test-machine.com",
                }
            response = self.client.post(reverse(views.cluster_settings, args=(user["username"], )), data)
            self.assertEqual(response.status_code, 200)
            self.assertIn("Settings Successfully Saved", response.content)


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
        keypair["private"] = keypair["private"][:50] + keypair["private"][53:]
        keypair["public"] = keypair["public"][:50] + keypair["public"][53:]
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
