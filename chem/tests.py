from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils import simplejson

import views
from models import ErrorReport

class MainPageTestCase(TestCase):
    names = ["24a_TON", "24b_TSP_24a_24a", "CON_24a"]

    def setUp(self):
        self.client = Client()

    def test_index(self):
        response = self.client.get(reverse("chem_index"))
        self.assertEqual(response.status_code, 200)

    def test_index_redirect(self):
        for name in self.names:
            url = reverse("chem_index") + "?molecule=%s" % name
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)

    def test_index_redirect(self):
        for name in self.names:
            for keywords in ["opt b3lyp/6-31g(d)", "td b3lyp/6-31g(d)"]:
                url = reverse("chem_index") + "?molecule=%s&keywords=%s" % (name, keywords)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)

    def test_molecule_detail(self):
        for name in self.names:
            response = self.client.get(reverse(views.gen_detail, args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_molecule_gjf(self):
        for name in self.names:
            response = self.client.get(reverse(views.write_gjf, args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_molecule_mol2(self):
        for name in self.names:
            response = self.client.get(reverse(views.write_mol2, args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_molecule_mol2(self):
        for name in self.names:
            response = self.client.get(reverse(views.write_png, args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_multi_molecule(self):
        names = ",".join(self.names)
        response = self.client.get(reverse(views.gen_multi_detail, args=(names, )))
        self.assertEqual(response.status_code, 200)

    def test_multi_molecule_zip(self):
        names = ",".join(self.names)
        response = self.client.get(reverse(views.gen_multi_detail_zip, args=(names, )))
        self.assertEqual(response.status_code, 200)

    def test_write_gjf(self):
        for name in self.names:
            response = self.client.get(reverse(views.write_gjf, args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_write_mol2(self):
        for name in self.names:
            response = self.client.get(reverse(views.write_mol2, args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_write_png(self):
        for name in self.names:
            response = self.client.get(reverse(views.write_png, args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_multi_job(self):
        response = self.client.get(reverse(views.multi_job))
        self.assertEqual(response.status_code, 200)

    def test_molecule_check(self):
        for name in self.names:
            response = self.client.get(reverse(views.molecule_check, args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_molecule_check_specific(self):
        names = [
            ("24ball_TON", "no rgroups allowed"),
            ("AA_TON", "can not attach to end"),
            ("A_TOO", "(1, 'Bad Core Name')"),
        ]
        for name, error in names:
            response = self.client.get(reverse(views.molecule_check, args=(name, )))
            values = simplejson.loads(response.content)["molecules"]
            self.assertEqual(values[0][2], error)

    def test_report_molecule(self):
        names = [
            "24242424242a_TON",
            "25252525252a_TON",
            "26262626262a_TON",
        ]
        data = {
            "email":"something@test.com",
            "message": "something something something something"
        }
        for name in names:
            for i in xrange(3):
                data["urgency"] = i
                response = self.client.get(reverse(views.molecule_check, args=(name, )))
                values = simplejson.loads(response.content)["molecules"]
                self.assertFalse(values[0][1])

                response = self.client.post(reverse(views.report, args=(name, )), data)
                self.assertEqual(response.status_code, 302)

                response = self.client.get(reverse(views.molecule_check, args=(name, )))
                values = simplejson.loads(response.content)["molecules"]
                self.assertTrue(values[0][1])

                obj = ErrorReport.objects.get(molecule=name)
                obj.delete()


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
