import os

from django.conf import settings
from django.test import Client, TestCase
from django.core.urlresolvers import reverse

import views
from project.utils import StringIO


class MainPageTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index(self):
        response = self.client.get(reverse(views.upload_data))
        self.assertEqual(response.status_code, 200)

    def test_log_parse(self):
        with open(os.path.join(settings.MEDIA_ROOT, "tests", "A_TON_A_A.log"), 'r') as f:
            data = {
                "myfiles": f,
                "option": "logparse",
            }
            response = self.client.post(reverse(views.upload_data), data)
            self.assertEqual(response.status_code, 200)
            results = response.content.split('\n')[1]
            expected = "A_TON_A_A.log,opt B3LYP/6-31g(d) geom=connectivity,-6.460873931,-1.31976745,41,0.0006,-567.1965205,---,0.35"
            self.assertEqual(results, expected)

