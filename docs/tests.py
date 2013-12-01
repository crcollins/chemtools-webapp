from django.test import Client, TestCase
from django.core.urlresolvers import reverse

import views


class DocsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index(self):
        response = self.client.get(reverse(views.index))
        self.assertEqual(response.status_code, 200)

    def test_common_errors(self):
        response = self.client.get(reverse(views.common_errors))
        self.assertEqual(response.status_code, 200)

    def test_one_liners(self):
        response = self.client.get(reverse(views.one_liners))
        self.assertEqual(response.status_code, 200)

    def test_technical(self):
        response = self.client.get(reverse(views.technical))
        self.assertEqual(response.status_code, 200)
