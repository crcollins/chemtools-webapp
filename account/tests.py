import os

from django.test import Client, TestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from Crypto.PublicKey import RSA
import mock

import views
import utils

from cluster.models import Cluster, Credential
from project.utils import SSHClient


SERVER = {
    "hostname": "localhost",
    "port": 2222,
    "username": "vagrant",
    "password": "vagrant",
}


def _register(client, data):
    response = client.post(reverse(views.register_user), data)
    assert response.status_code == 200
    content = response.content
    start = content.index("Please click")
    end = content.index("this", start) - 2
    url = content[start:end].split('href="')[1]
    key = url.split('register/')[1]
    response = client.get(reverse(views.activate_user, args=(key, )))
    assert response.status_code == 200
    v = client.login(username=data["username"], password=data["new_password1"])
    assert v
    client.logout()
    return key


class RegistrationTestCase(TestCase):

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
            new_user = get_user_model().objects.create_user(user["username"],
                                                user["email"],
                                                user["new_password1"])
            new_user.save()

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
        self.assertRaises(ValueError, _register, self.client, data)

    def test_register_bad_password(self):
        data = {
            "username": "testmanpass",
            "email": "testmanpass@test.com",
            "new_password1": "mypass",
            "new_password2": "mypass123",
        }
        self.assertRaises(ValueError, _register, self.client, data)

    def test_register_after_login(self):
        for user in self.users:
            r = self.client.login(
                username=user["username"],
                password=user["new_password1"])
            self.assertTrue(r)
            response = self.client.get(reverse(views.register_user))
            self.assertEqual(response.status_code, 302)

    def test_activation_page_after_activated(self):
        data = {
            "username": "testmankey",
            "email": "testmankey@test.com",
            "new_password1": "mypass",
            "new_password2": "mypass",
        }
        key = _register(self.client, data)
        response = self.client.get(reverse(views.activate_user, args=(key, )))
        self.assertEqual(response.status_code, 302)


class SettingsTestCase(TestCase):
    users = [{
        "username": "vagrant",
        "email": "user1@test.com",
        "new_password1": "mypass",
        "new_password2": "mypass",
    }, {
        "username": "user2",
        "email": "user2@test.com",
        "new_password1": "mypass",
        "new_password2": "mypass",
    }]

    def setUp(self):
        self.client = Client()
        for user_info in self.users:
            new_user = get_user_model().objects.create_user(user_info["username"],
                                                user_info["email"],
                                                user_info["new_password1"])
            new_user.save()

    def test_get_public_key(self):
        for user_info in self.users:
            response = self.client.get(reverse(views.get_public_key,
                                               args=(user_info["username"], )))
            self.assertEqual(response.status_code, 200)
            user = get_user_model().objects.get(username=user_info["username"])
            self.assertEqual(response.content.strip(), user.public_key)

    def test_get_public_key_invalid(self):
        response = self.client.get(reverse(views.get_public_key,
                                           args=("notauser", )))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.strip(), '')

    def test_settings_redirect_page(self):
        for user_info in self.users:
            r = self.client.login(
                username=user_info["username"],
                password=user_info["new_password1"])
            self.assertTrue(r)
            response = self.client.get(reverse(views.user_settings,
                                               args=(user_info["username"], )))
            self.assertEqual(response.status_code, 302)

    def test_change_settings_page(self):
        for user_info in self.users:
            r = self.client.login(
                username=user_info["username"],
                password=user_info["new_password1"])
            self.assertTrue(r)
            response = self.client.get(reverse(views.account_page,
                                               args=(user_info["username"],
                                                     "settings")))
            self.assertEqual(response.status_code, 200)

    def test_change_settings_redirect(self):
        for i, user_info in enumerate(self.users):
            r = self.client.login(
                username=user_info["username"],
                password=user_info["new_password1"])
            self.assertTrue(r)
            opposite = self.users[not i]["username"]
            response = self.client.get(reverse(views.account_page,
                                               args=(opposite, "settings")))
            self.assertEqual(response.status_code, 302)

    def test_change_email(self):
        for user_info in self.users:
            r = self.client.login(
                username=user_info["username"],
                password=user_info["new_password1"])
            self.assertTrue(r)

            response = self.client.get(reverse(views.account_page,
                                               args=(user_info["username"],
                                                     "settings")))
            self.assertEqual(response.status_code, 200)

            data = {"email": 'a' + user_info["email"]}
            response = self.client.post(reverse(views.account_page,
                                                args=(user_info["username"],
                                                      "settings")),
                                        data)
            self.assertIn("Settings Successfully Saved", response.content)

            user = get_user_model().objects.get(username=user_info["username"])
            self.assertEqual(user.email, 'a' + user_info["email"])
            user.email = user_info["email"]
            user.save()

    def test_change_xsede_username(self):
        for user_info in self.users:
            r = self.client.login(username=user_info["username"],
                                  password=user_info["new_password1"])
            self.assertTrue(r)

            response = self.client.get(reverse(views.account_page,
                                               args=(user_info["username"],
                                                     "settings")))
            self.assertEqual(response.status_code, 200)

            data = {"xsede_username": user_info["username"], "email": user_info["email"]}
            response = self.client.post(reverse(views.account_page,
                                                args=(user_info["username"], "settings")), data)
            self.assertIn("Settings Successfully Saved", response.content)

            user = get_user_model().objects.get(username=user_info["username"])
            self.assertEqual(user.xsede_username, user_info["username"])

    def test_change_password(self):
        for user_info in self.users:
            r = self.client.login(username=user_info["username"],
                                  password=user_info["new_password1"])
            self.assertTrue(r)

            response = self.client.get(reverse(views.account_page,
                                               args=(user_info["username"],
                                                     "password")))
            self.assertEqual(response.status_code, 200)
            data = {
                "old_password": user_info["new_password1"],
                "new_password1": user_info["new_password1"] + 'a',
                "new_password2": user_info["new_password2"] + 'a',
            }
            response = self.client.post(reverse(views.account_page,
                                                args=(user_info["username"],
                                                      "password")),
                                        data)
            self.assertEqual(response.status_code, 200)
            self.assertIn("Settings Successfully Saved", response.content)
            self.client.logout()

            r = self.client.login(username=user_info["username"],
                                  password=user_info["new_password1"] + 'a')
            self.assertTrue(r)
            user = get_user_model().objects.get(username=user_info["username"])
            user.set_password(user_info["new_password1"])

    def test_change_password_fail(self):
        for user_info in self.users:
            r = self.client.login(username=user_info["username"],
                                  password=user_info["new_password1"])
            self.assertTrue(r)

            response = self.client.get(reverse(views.account_page,
                                               args=(user_info["username"],
                                                     "password")))
            self.assertEqual(response.status_code, 200)
            data = {
                "old_password": user_info["new_password1"],
                "new_password1": user_info["new_password1"] + 'a',
                "new_password2": user_info["new_password2"],
            }
            self.assertNotIn("The two password fields", response.content)
            response = self.client.post(reverse(views.account_page,
                                                args=(user_info["username"],
                                                      "password")),
                                        data)
            self.assertEqual(response.status_code, 200)
            self.assertIn("The two password fields", response.content)


def build_mock_connections(obj):
    patcher_ssh = mock.patch('cluster.models.get_ssh_connection')
    obj.addCleanup(patcher_ssh.stop)

    mock_ssh = mock.MagicMock(SSHClient, name='SSH', autospec=True)
    mock_ssh_conn = patcher_ssh.start()
    mock_ssh_conn.return_value = mock_ssh
    return mock_ssh


class SSHKeyTestCase(TestCase):
    cluster = {
        "name": "test-machine",
        "hostname": "localhost",
        "port": 2222,
    }
    credential = {
        "username": "vagrant",
        "use_password": False,
    }
    users = [{
        "username": "vagrant",
        "email": "user1@test.com",
        "new_password1": "mypass",
        "new_password2": "mypass",
    }, {
        "username": "user2",
        "email": "user2@test.com",
        "new_password1": "mypass",
        "new_password2": "mypass",
    }]

    def setUp(self):
        self.mock_ssh = build_mock_connections(self)
        self.client = Client()
        for user in self.users:
            new_user = get_user_model().objects.create_user(user["username"],
                                                user["email"],
                                                user["new_password1"])
            new_user.save()

        user = get_user_model().objects.all()[0]
        profile = user
        test_path = os.path.join(settings.MEDIA_ROOT, "tests")
        with open(os.path.join(test_path, "id_rsa.pub"), 'r') as f:
            profile.public_key = f.read()
        with open(os.path.join(test_path, "id_rsa"), 'r') as f:
            profile.private_key = f.read()
        profile.save()

        cluster = Cluster(
            name=self.cluster["name"],
            hostname=self.cluster["hostname"],
            port=self.cluster["port"])
        cluster.save()
        self.cluster = cluster
        credential = Credential(
            user=user,
            cluster=cluster,
            username=self.credential["username"],
            password='',
            use_password=False)
        credential.save()
        self.credential = credential
        credential2 = Credential(
            user=user,
            cluster=cluster,
            username=self.credential.username,
            password="vagrant",
            use_password=True)
        credential2.save()
        self.credential2 = credential2

    def test_change_ssh_key(self):
        user = self.users[1]
        profile = get_user_model().objects.get(username=user["username"])
        r = self.client.login(username=user["username"],
                              password=user["new_password1"])
        self.assertTrue(r)

        response = self.client.get(reverse(views.account_page,
                                           args=(user["username"],
                                                 "settings")))
        self.assertEqual(response.status_code, 200)

        initial = profile.public_key
        data = {"new_ssh_keypair": "on", "email": user["email"]}
        response = self.client.post(reverse(views.account_page,
                                            args=(user["username"],
                                                  "settings")),
                                    data)
        self.assertIn("Settings Successfully Saved", response.content)

        profile = get_user_model().objects.get(username=user["username"])
        self.assertNotEqual(profile.public_key, initial)

    def test_update_ssh_keys(self):
        user = self.users[0]
        profile = get_user_model().objects.get(username=user["username"])
        r = self.client.login(username=user["username"],
                              password=user["new_password1"])
        self.assertTrue(r)

        response = self.client.get(reverse(views.account_page,
                                           args=(user["username"],
                                                 "settings")))
        self.assertEqual(response.status_code, 200)

        initial = profile.public_key
        data = {"new_ssh_keypair": "on", "email": user["email"]}
        response = self.client.post(reverse(views.account_page,
                                            args=(user["username"],
                                                  "settings")),
                                    data)
        self.assertIn("Settings Successfully Saved", response.content)
        profile = get_user_model().objects.get(username=user["username"])
        self.assertNotEqual(profile.public_key, initial)
        self.credential.get_ssh_connection()


class LoginTestCase(TestCase):

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
            new_user = get_user_model().objects.create_user(user["username"],
                                                user["email"],
                                                user["new_password1"])
            new_user.save()

    def test_login(self):
        for user in self.users:
            response = self.client.get("/login/")
            self.assertEqual(response.status_code, 200)

            data = {
                "username": user["username"],
                "password": user["new_password1"],
            }
            response = self.client.post("/login/", data)
            self.assertEqual(response.status_code, 302)

    def test_invalid_username(self):
        for user in self.users:
            response = self.client.get("/login/")
            self.assertEqual(response.status_code, 200)

            data = {
                "username": user["username"] + 'a',
                "password": user["new_password1"],
            }
            response = self.client.post("/login/", data)
            self.assertEqual(response.status_code, 200)
            self.assertIn("alert-danger", response.content)

    def test_invalid_password(self):
        for user in self.users:
            response = self.client.get("/login/")
            self.assertEqual(response.status_code, 200)

            data = {
                "username": user["username"],
                "password": user["new_password1"] + 'a',
            }
            response = self.client.post("/login/", data)
            self.assertEqual(response.status_code, 200)
            self.assertIn("alert-danger", response.content)

    def test_logout(self):
        for user in self.users:
            r = self.client.login(username=user["username"],
                                  password=user["new_password1"])
            self.assertTrue(r)

            data = {
                "username": user["username"],
                "password": user["new_password1"],
            }
            response = self.client.get("/logout/", data)
            self.assertEqual(response.status_code, 200)


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
        private = b"thisisnotavalidprivatekey"
        public = b"thisisnotavalidpublickey"
        self.assertRaises(ValueError, RSA.importKey, (private, ))
        self.assertRaises(ValueError, RSA.importKey, (public, ))

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
