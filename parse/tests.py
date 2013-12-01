from django.test import Client, TestCase
from django.core.urlresolvers import reverse

import views


class MainPageTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index(self):
        response = self.client.get(reverse(views.upload_data))
        self.assertEqual(response.status_code, 200)
