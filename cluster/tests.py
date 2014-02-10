from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils import simplejson

import views
from project.utils import get_sftp_connection, get_ssh_connection, AESCipher


class SSHPageTestCases(TestCase):
    def setUp(self):
        user = User.objects.create_user("testerman", email="test@test.com", password="S0m3thing")
        user.save()
        self.client = Client()

    def test_job_index(self):
        response = self.client.get(reverse(views.job_index))
        self.assertEqual(response.status_code, 302)

        r = self.client.login(username="testerman", password="S0m3thing")
        self.assertTrue(r)
        response = self.client.get(reverse(views.job_index))
        self.assertEqual(response.status_code, 200)

    def test_get_job_list(self):
        response = self.client.get(reverse(views.get_job_list))
        self.assertEqual(response.status_code, 302)

    def test_get_job_list_auth(self):
        user = User.objects.get(username="testerman")
        r = self.client.login(username="testerman", password="S0m3thing")
        self.assertTrue(r)

        response = self.client.get(reverse(views.get_job_list))
        self.assertEqual(response.status_code, 200)
        data = simplejson.loads(response.content)
        self.assertTrue(data["is_authenticated"])



class UtilsTestCase(TestCase):
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
