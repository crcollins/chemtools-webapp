import zipfile
import itertools
import urllib

from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils import simplejson

from project.utils import StringIO
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
            for keywords in ["opt HF/6-31g(d)", "td b3lyp/6-31g(d)"]:
                params = "?molecule=%s&keywords=%s" % (name, keywords)
                url = reverse("chem_index") + params
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)

    def test_molecule_detail(self):
        for name in self.names:
            response = self.client.get(reverse(views.molecule_detail, args=(name, )))
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
        response = self.client.get(reverse(views.multi_molecule, args=(names, )))
        self.assertEqual(response.status_code, 200)

    def test_multi_molecule_zip(self):
        names = ",".join(self.names)
        gjfnames = set([name + ".gjf" for name in self.names])
        response = self.client.get(reverse(views.multi_molecule_zip, args=(names, )))
        self.assertEqual(response.status_code, 200)
        with StringIO(response.content) as f:
            with zipfile.ZipFile(f, "r") as zfile:
                self.assertEqual(set(zfile.namelist()), gjfnames)

    def test_multi_molecule_zip_options(self):
        names = ",".join(self.names)
        sets = {
            "gjf": set([name + ".gjf" for name in self.names]),
            "image": set([name + ".png" for name in self.names]),
            "mol2": set([name + ".mol2" for name in self.names]),
            "": set(),
        }

        for group in itertools.product(["gjf", ""], ["image", ""], ["mol2", ""]):
            params = '?' + '&'.join([x + "=true" for x in group if x])
            if params == '?':  # remove the blank case
                continue
            comparenames = set()
            for x in group:
                comparenames |= sets[x]
            url = reverse(views.multi_molecule_zip, args=(names, )) + params

            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            with StringIO(response.content) as f:
                with zipfile.ZipFile(f, "r") as zfile:
                    self.assertEqual(set(zfile.namelist()), comparenames)

    def test_write_gjf(self):
        for name in self.names:
            response = self.client.get(reverse(views.write_gjf, args=(name, )))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get('Content-Disposition'),
                "attachment; filename=%s.gjf" % name)
            string = "%%nprocshared=16\n%%mem=59GB\n%%chk=%s.chk\n# opt B3LYP/6-31g(d) geom=connectivity"
            self.assertTrue(response.content.startswith(string % name))

    def test_write_gjf_keywords(self):
        for name in self.names:
            for keywords in ["opt HF/6-31g(d)", "td b3lyp/6-31g(d)"]:
                params = "?keywords=%s" % keywords
                url = reverse(views.write_gjf, args=(name, )) + params
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.get('Content-Disposition'),
                    "attachment; filename=%s.gjf" % name)
                string = "%%nprocshared=16\n%%mem=59GB\n%%chk=%s.chk\n# %s geom=connectivity"
                self.assertTrue(response.content.startswith(string % (name, keywords)))

    def test_write_mol2(self):
        for name in self.names:
            response = self.client.get(reverse(views.write_mol2, args=(name, )))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get('Content-Disposition'),
                "attachment; filename=%s.mol2" % name)
            string = "@<TRIPOS>MOLECULE"
            self.assertTrue(response.content.startswith(string))

    def test_write_png(self):
        for name in self.names:
            response = self.client.get(reverse(views.write_png, args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_multi_job(self):
        response = self.client.get(reverse(views.multi_job))
        self.assertEqual(response.status_code, 200)
        options = {
            "filenames": '\n'.join(self.names),
            "name": "{{ name }}",
            "email": "test@test.com",
            "nodes": 1,
            "walltime": 48,
            "allocation": "TG-CHE120081",
            "cluster": 'g',
            "template": "{{ name }} {{ email }} {{ nodes }} {{ walltime }} {{ allocation }}",
        }
        url = reverse(views.multi_job) + '?' + urllib.urlencode(options)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        with StringIO(response.content) as f:
            with zipfile.ZipFile(f, "r") as zfile:
                names = set([x + ".gjob" for x in self.names])
                self.assertEqual(set(zfile.namelist()), names)

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
            "email": "something@test.com",
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
