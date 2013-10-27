from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

import views

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
