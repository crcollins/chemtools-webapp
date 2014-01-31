from itertools import product

from django.test import Client, TestCase
from django.core.urlresolvers import reverse

import views
import models
from chemtools.utils import RGROUPS, XGROUPS, ARYL, CLUSTERS


class FragmentTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index(self):
        response = self.client.get(reverse(views.frag_index))
        self.assertEqual(response.status_code, 200)

    def test_detail_ends(self):
        for frag in RGROUPS + ARYL:
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


class ModelTestCase(TestCase):
    def setUp(self):
        new_data = models.DataPoint(name="A_TON_A_A", exact_name="A_TON_A_A_n1_m1_x1_y1_z1",
                    options="td B3LYP/6-31g(d) geom=connectivity", homo=-6.460873931,
                    lumo=-1.31976745, homo_orbital=41, dipole=0.0006,
                    energy=-567.1965205, band_gap=4.8068)
        new_data.save()

    def test_datapoint_unicode(self):
        string = str(models.DataPoint.objects.all()[0])
        self.assertEqual(string, "A_TON_A_A_n1_m1_x1_y1_z1")