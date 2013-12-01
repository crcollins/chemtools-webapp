from itertools import product

from django.test import Client, TestCase
from django.core.urlresolvers import reverse

import views
from chemtools.utils import RGROUPS, XGROUPS, ARYL, CLUSTERS


class FragmentTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index(self):
        response = self.client.get(reverse(views.frag_index))
        self.assertEqual(response.status_code, 200)

    def test_detail_ends(self):
        for frag in RGROUPS + ARYL + XGROUPS:
            response = self.client.get(reverse(views.get_frag, args=(frag, )))
            self.assertEqual(response.status_code, 200)

    def test_detail_cores(self):
        for frag in (''.join(x) for x in product("EZTC", "234", "34")):
            response = self.client.get(reverse(views.get_frag, args=(frag, )))
            self.assertEqual(response.status_code, 200)


class TemplateTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index(self):
        response = self.client.get(reverse(views.template_index))
        self.assertEqual(response.status_code, 200)

    def test_detail(self):
        for cluster in CLUSTERS:
            response = self.client.get(reverse(views.get_template, args=(cluster, )))
            self.assertEqual(response.status_code, 200)
