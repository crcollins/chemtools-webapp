from itertools import product
import os

import numpy
from django.conf import settings
from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.core.management import call_command

import views
import models
import load_data
from chemtools.constants import RGROUPS, XGROUPS, ARYL


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

    def test_frag_redirect(self):
        response = self.client.get(reverse(views.get_frag,
                                            args=("notafragment", )))
        self.assertEqual(response.status_code, 302)

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


class ModelTestCase(TestCase):
    def setUp(self):
        new_data = models.DataPoint(
                                name="A_TON_A_A",
                                exact_name="A_TON_A_A_n1_m1_x1_y1_z1",
                                options="td B3LYP/6-31g(d) geom=connectivity",
                                homo=-6.460873931,
                                lumo=-1.31976745,
                                homo_orbital=41,
                                dipole=0.0006,
                                energy=-567.1965205,
                                band_gap=4.8068)
        new_data.save()
        new_data2 = models.DataPoint(
                                name="Garbage",
                                exact_name="Garbage",
                                options="Nothing",
                                homo=1.0,
                                lumo=2.0,
                                homo_orbital=42,
                                dipole=0.0,
                                energy=100.0,
                                band_gap=2.0,
                                decay_feature="[1,2,3]")
        new_data2.save()

    def test_datapoint_unicode(self):
        string = str(models.DataPoint.objects.all()[0])
        self.assertEqual(string, "A_TON_A_A")

    def test_get_all_data(self):
        FEATURE, HOMO, LUMO, GAP = models.DataPoint.get_all_data()
        self.assertTrue((FEATURE == numpy.matrix([[1,2,3]])).all())
        self.assertTrue((HOMO == numpy.matrix([[1.0]])).all())
        self.assertTrue((LUMO == numpy.matrix([[2.0]])).all())
        self.assertTrue((GAP == numpy.matrix([[2.0]])).all())


class LoadDataTestCase(TestCase):
    def test_load_data(self):
        path = os.path.join(settings.MEDIA_ROOT, "tests", "data.csv")
        load_data.main(path)

    def test_load_data_command(self):
        path = os.path.join(settings.MEDIA_ROOT, "tests", "data.csv")
        call_command('load_data', path)
