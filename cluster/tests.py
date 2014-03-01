import os

from django.conf import settings
from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils import simplejson

import views
import models
import utils
import interface
from account.views import account_page
from project.utils import get_sftp_connection, get_ssh_connection, AESCipher, \
                        SSHClient, SFTPClient


class SSHPageTestCase(TestCase):
    user = {
        "username": "testerman",
        "email": "test@test.com",
        "password": "S0m3thing",
    }
    super_user = {
        "username": "admin",
        "email": "admin@test.com",
        "password": "cantstopmenow",
    }
    cluster = {
            "name": "test-machine",
            "hostname": "localhost",
            "port": 2222,
        }
    credential = {
        "username": "vagrant",
        "password": "vagrant",
        "password2": "vagrant",
        "use_password": True,
    }
    credential2 = {
        "username": "vagrant",
        "password": "vagrant",
        "password2": "vagrant",
        "use_password": True,
    }

    def setUp(self):
        user = User.objects.create_user(**self.user)
        user.save()
        super_user = User.objects.create_superuser(**self.super_user)
        super_user.save()

        cluster = models.Cluster(
                                name=self.cluster["name"],
                                hostname=self.cluster["hostname"],
                                port=self.cluster["port"])
        cluster.save()
        self.cluster = cluster
        credential = models.Credential(
                                        user=user,
                                        cluster=cluster,
                                        username=self.credential["username"],
                                        password=self.credential["password"],
                                        use_password=True)
        credential.save()
        self.credential = credential

        credential2 = models.Credential(
                                        user=super_user,
                                        cluster=cluster,
                                        username=self.credential2["username"],
                                        password=self.credential2["password"],
                                        use_password=True)
        credential2.save()
        self.credential2 = credential2

        self.client = Client()

    def test_job_index(self):
        response = self.client.get(reverse(views.job_index))
        self.assertEqual(response.status_code, 302)

        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)
        response = self.client.get(reverse(views.job_index))
        self.assertEqual(response.status_code, 200)

    def test_cluster_job_index(self):
        url = reverse(views.cluster_job_index, args=(self.cluster.name, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_job_detail(self):
        url = reverse(views.job_detail, args=(self.cluster.name, 1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_job_detail_fail(self):
        url = reverse(views.job_detail, args=(self.cluster.name, 100000000000))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("That job number is not running.", response.content)

    def test_get_job_list(self):
        response = self.client.get(reverse(views.get_job_list))
        self.assertEqual(response.status_code, 302)

    def test_get_job_list_auth(self):
        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)

        response = self.client.get(reverse(views.get_job_list))
        self.assertEqual(response.status_code, 200)
        data = simplejson.loads(response.content)
        self.assertTrue(data["is_authenticated"])

    def test_kill_job(self):
        url = reverse(views.kill_job, args=("test-machine", ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        r = self.client.login(username=self.super_user["username"],
                            password=self.super_user["password"])
        self.assertTrue(r)

        gjfstring = "EMPTY"
        jobstring = "sleep 60"
        results = interface.run_job(self.credential2, gjfstring, jobstring)
        self.assertIsNone(results["error"])
        jobid = results["jobid"]
        data = {
            results["jobid"]: "on",
        }
        response = self.client.post(url, data)

    def test_kill_job_perm_fail(self):
        url = reverse(views.kill_job, args=("test-machine", ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)
        data = {
            "123": "on",
            "234": "on",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content,
                        "You must be a staff user to kill a job.")



class SSHSettingsTestCase(TestCase):
    user = {
        "username": "testerman",
        "email": "test@test.com",
        "password": "S0m3thing",
    }
    cluster = {
            "name": "test-machine",
            "hostname": "localhost",
            "port": 2222,
        }
    credential = {
        "username": "vagrant",
        "password": "vagrant",
        "password2": "vagrant",
        "use_password": True,
    }
    credential2 = {
        "username": "vagrant",
        "use_password": False,
    }

    def setUp(self):
        user = User.objects.create_user(self.user["username"],
                                        email=self.user["email"],
                                        password=self.user["password"])
        user.save()
        profile = user.get_profile()
        test_path = os.path.join(settings.MEDIA_ROOT, "tests")
        with open(os.path.join(test_path, "id_rsa.pub"), 'r') as f:
            profile.public_key = f.read()
        with open(os.path.join(test_path, "id_rsa"), 'r') as f:
            profile.private_key = f.read()
        profile.save()

        cluster = models.Cluster(
                                name=self.cluster["name"],
                                hostname=self.cluster["hostname"],
                                port=self.cluster["port"])
        cluster.save()
        self.cluster = cluster
        credential = models.Credential(
                                        user=user,
                                        cluster=cluster,
                                        username=self.credential["username"],
                                        password=self.credential["password"],
                                        use_password=True)
        credential.save()
        self.credential = credential
        credential2 = models.Credential(
                                        user=user,
                                        cluster=cluster,
                                        username=self.credential2["username"],
                                        password='',
                                        use_password=False)
        credential2.save()
        self.credential2 = credential2
        self.client = Client()

    def test_add_cluster(self):
        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)

        url = reverse(account_page, args=(self.user["username"], "clusters"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = {
            "name": "test-machine",
            "hostname": "test-machine.com",
            "port": 22,
            }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Settings Successfully Saved", response.content)

    def test_add_credential_invalid(self):
        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)

        data = {
            "username": "vagrant",
            "password": "incorrect",
            "password2": "incorrect",
            "cluster": self.cluster.id,
            "use_password": True,
        }
        url = reverse(account_page, args=(self.user["username"],
                                        "credentials"))
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Those credentials did not work.", response.content)

    def test_add_credential_password(self):
        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)
        url = reverse(account_page, args=(self.user["username"],
                                        "credentials"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "username": "vagrant",
            "password": "vagrant",
            "password2": "vagrant",
            "cluster": self.cluster.id,
            "use_password": True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Settings Successfully Saved", response.content)

    def test_add_credential_invalid_password(self):
        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)

        url = reverse(account_page, args=(self.user["username"],
                                        "credentials"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "username": "vagrant",
            "password": "incorrect",
            "password2": "password",
            "cluster": self.cluster.id,
            "use_password": True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Your passwords do not match", response.content)

    def test_add_credential_key(self):
        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)

        url = reverse(account_page, args=(self.user["username"],
                                        "credentials"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "username": "vagrant",
            "cluster": self.cluster.id,
            "use_password": False,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Settings Successfully Saved", response.content)

    def test_delete_credential(self):
        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)

        url = reverse(account_page, args=(self.user["username"],
                                        "credentials"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "delete": "on",
            "vagrant@localhost:2222-1": "on",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Settings Successfully Saved", response.content)

    def test_delete_credential_invalid(self):
        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)

        url = reverse(account_page, args=(self.user["username"],
                                        "credentials"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "delete": "on",
            "sd@meh:22-1": "on",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Settings Successfully Saved", response.content)

    def test_delete_multi_credential(self):
        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)

        url = reverse(account_page, args=(self.user["username"],
                                        "credentials"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "delete": "on",
            "vagrant@localhost:2222-1": "on",
            "vagrant@localhost:2222-2": "on",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Settings Successfully Saved", response.content)

    def test_credential_ssh(self):
        with self.credential.get_ssh_connection():
            pass
        with self.credential2.get_ssh_connection():
            pass

    def test_credential_sftp(self):
        with self.credential.get_sftp_connection():
            pass
        with self.credential2.get_sftp_connection():
            pass

    def test_get_ssh_connection_obj(self):
        ssh = self.credential.get_ssh_connection()
        obj = utils.get_ssh_connection_obj(self.credential)
        self.assertTrue(isinstance(obj, SSHClient))

    def test_get_ssh_connection_obj_SSHClient(self):
        ssh = self.credential.get_ssh_connection()
        self.assertEqual(utils.get_ssh_connection_obj(ssh), ssh)

    def test_get_ssh_connection_obj_fail(self):
        obj = []
        with self.assertRaises(TypeError):
            utils.get_ssh_connection_obj(obj)

    def test_get_sftp_connection_obj(self):
        sftp = self.credential.get_sftp_connection()
        obj = utils.get_sftp_connection_obj(self.credential)
        self.assertTrue(isinstance(obj, SFTPClient))

    def test_get_sftp_connection_obj_SFTPClient(self):
        sftp = self.credential.get_sftp_connection()
        self.assertEqual(utils.get_sftp_connection_obj(sftp), sftp)

    def test_get_sftp_connection_obj_fail(self):
        obj = []
        with self.assertRaises(TypeError):
            utils.get_sftp_connection_obj(obj)


class UtilsTestCase(TestCase):
    def test_get_sftp_password(self):
        sftp = get_sftp_connection("localhost", "vagrant",
                                password="vagrant", port=2222)
        with sftp:
            pass

    def test_get_sftp_key(self):
        test_path = os.path.join(settings.MEDIA_ROOT, "tests")
        with open(os.path.join(test_path, "id_rsa"), 'r') as key:
            sftp = get_sftp_connection("localhost", "vagrant",
                                    key=key, port=2222)
            with sftp:
                pass

    def test_get_sftp_error(self):
        with self.assertRaises(Exception):
            with get_sftp_connection("localhost", "username"):
                pass

    def test_get_ssh_password(self):
        ssh = get_ssh_connection("localhost", "vagrant",
                                password="vagrant", port=2222)
        with ssh:
            pass

    def test_get_ssh_key(self):
        test_path = os.path.join(settings.MEDIA_ROOT, "tests")
        with open(os.path.join(test_path, "id_rsa"), 'r') as key:
            ssh = get_ssh_connection("localhost", "vagrant",
                                    key=key, port=2222)
            with ssh:
                pass

    def test_get_ssh_error(self):
        with self.assertRaises(Exception):
            get_ssh_connection("localhost", "username")

    def test_AES(self):
        cipher = AESCipher()
        string = "The quick brown fox jumps over the lazy dog."
        ct = cipher.encrypt(string)
        pt = cipher.decrypt(ct)
        self.assertEqual(pt, string)

    def test_AES_error(self):
        cipher = AESCipher()
        string = "The quick brown fox jumps over the lazy dog."
        ct = cipher.encrypt(string)[:10] + "randomgarbage"
        self.assertRaises(TypeError, cipher.decrypt, ct)
