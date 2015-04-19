from itertools import product
import os

import numpy
from django.conf import settings
from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.core.files import File

import views
import models
import load_data
from account.views import account_page
from chemtools.constants import RGROUPS, ARYL
from project.utils import StringIO


OPTIONS = {
    "name": "{{ name }}",
    "email": "test@test.com",
    "nodes": 1,
    "walltime": 48,
    "allocation": "TG-CHE120081",
    "template":
            "{{ name }} {{ email }} {{ nodes }} {{ time }} {{ allocation }}",
}
USER_LOGIN = {
    "username": "testerman",
    "password": "S0m3thing",
}
USER = USER_LOGIN.copy()
USER["email"] = "test@test.com"

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
        user = get_user_model().objects.create_user(**USER)
        user.save()
        self.user = user

        self.template = models.JobTemplate(
                                        name="test-template-delete",
                                        creator=self.user,
                                        )
        self.template.template = File(StringIO("template", name="test-template-delete"))
        self.template.save()

    def test_index(self):
        response = self.client.get(reverse(views.template_index))
        self.assertEqual(response.status_code, 200)

    def test_add_template(self):
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)

        url = reverse(account_page, args=(USER["username"], "templates"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = {
            "name": "test-template",
            "creator": self.user,
            "template": "asda",
            "save": True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Settings Successfully Saved", response.content)

    def test_save_template(self):
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)

        url = reverse(account_page, args=(USER["username"], "templates"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "name": "test-template",
            "creator": self.user,
            "template": "asda",
            "save": True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Settings Successfully Saved", response.content)

        data = {
            "name": "test-template",
            "creator": self.user,
            "template": "new stuff",
            "save": True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Settings Successfully Saved", response.content)
        obj = models.JobTemplate.objects.get(name="test-template")
        self.assertEqual(obj.template.read(), "new stuff")

    def test_delete_template(self):
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)

        url = reverse(account_page, args=(USER["username"], "templates"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        name = models.JobTemplate.objects.filter(name="test-template-delete")[0].get_long_name()
        data = {
            "delete": "on",
            name : "on",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Settings Successfully Saved", response.content)
        try:
            models.JobTemplate.objects.get(name="test-template-delete")
            self.assertTrue(False)
        except models.JobTemplate.DoesNotExist:
            pass


class ModelTestCase(TestCase):

    def setUp(self):
        new_vector = models.FeatureVector(
            type=1, exact_name="A_TON_A_A_n1_m1_x1_y1_z1", vector=[1, 2, 3])
        new_vector.save()
        new_vector2 = models.FeatureVector(
            type=2, exact_name="Garbage", vector=[1])
        new_vector2.save()
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
        new_data.vectors.add(new_vector)
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
            band_gap=2.0)
        new_data2.save()
        new_data2.vectors.add(new_vector2)
        new_data2.save()

    def test_datapoint_unicode(self):
        string = str(models.DataPoint.objects.all()[0])
        self.assertEqual(string, "A_TON_A_A")

    def test_get_all_data(self):
        FEATURE, HOMO, LUMO, GAP = models.DataPoint.get_all_data()
        self.assertTrue((FEATURE == numpy.matrix([[1, 2, 3]])).all())
        self.assertTrue((HOMO == numpy.matrix([[-6.460873931]])).all())
        self.assertTrue((LUMO == numpy.matrix([[-1.31976745]])).all())
        self.assertTrue((GAP == numpy.matrix([[4.8068]])).all())

    def test_get_all_data_no_default(self):
        FEATURE, HOMO, LUMO, GAP = models.DataPoint.get_all_data(type=2)
        self.assertTrue((FEATURE == numpy.matrix([[1]])).all())
        self.assertTrue((HOMO == numpy.matrix([[1.0]])).all())
        self.assertTrue((LUMO == numpy.matrix([[2.0]])).all())
        self.assertTrue((GAP == numpy.matrix([[2.0]])).all())

    def test_jobtemplate(self):
        data = OPTIONS.copy()
        data["custom_template"] = True
        string = models.JobTemplate.render(**data)
        expected = "{{ name }} test@test.com 1 48:00:00 TG-CHE120081"
        self.assertEqual(string, expected)

    def test_jobtemplate_base(self):
        data = OPTIONS.copy()
        data["custom_template"] = False
        data['base_template'] = models.JobTemplate.objects.get(
            name="Localhost")
        data['template'] = None
        string = models.JobTemplate.render(**data)
        self.assertIn(data["name"], string)

    def test_jobtemplate_base_multi(self):
        template = models.JobTemplate.objects.get(name="Localhost")
        data = OPTIONS.copy()
        data["custom_template"] = False
        data['base_template'] = template
        data['template'] = None
        string = models.JobTemplate.render(**data)
        self.assertTrue(string != '')
        self.assertIn(data["name"], string)

        string2 = models.JobTemplate.render(**data)
        self.assertTrue(string2 != '')
        self.assertIn(data["name"], string)


class LoadDataTestCase(TestCase):

    def test_load_data(self):
        path = os.path.join(settings.MEDIA_ROOT, "tests", "data.csv")
        with open(path, 'r') as f:
            load_data.main(f)

    def test_load_data_long(self):
        path = os.path.join(settings.MEDIA_ROOT, "tests", "data_long.csv")
        with open(path, 'r') as f:
            load_data.main(f)

    def test_load_data_command(self):
        path = os.path.join(settings.MEDIA_ROOT, "tests", "data.csv")
        call_command('load_data', path)
