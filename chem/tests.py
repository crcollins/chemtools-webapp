import os
import zipfile
import itertools
import urllib

from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.contrib.auth.models import User
from django.conf import settings

from project.utils import StringIO
from data.models import DataPoint
from cluster.models import Cluster, Credential
from chemtools.constants import KEYWORDS
import views

from models import ErrorReport


class MainPageTestCase(TestCase):
    names = ["24a_TON", "24b_TSP_24a_24a", "CON_24a", "A_TON_A_A", "TON_CCC"]
    options = {
        "job": True,
        "name": "{{ name }}",
        "email": "test@test.com",
        "nodes": 1,
        "walltime": 48,
        "allocation": "TG-CHE120081",
        "cluster": 'g',
        "template":
            "{{ name }} {{ email }} {{ nodes }} {{ time }} {{ allocation }}",
    }

    def setUp(self):
        self.client = Client()
        self.user = {
            "username": "user1",
            "email": "user1@test.com",
            "password": "mypass",
        }
        new_user = User.objects.create_user(self.user["username"],
                                            self.user["email"],
                                            self.user["password"])
        new_user.save()
        new_data = DataPoint(name="A_TON_A_A",
                            exact_name="A_TON_A_A_n1_m1_x1_y1_z1",
                            options="td B3LYP/6-31g(d) geom=connectivity",
                            homo=-6.460873931,
                            lumo=-1.31976745,
                            homo_orbital=41,
                            dipole=0.0006,
                            energy=-567.1965205,
                            band_gap=4.8068)
        new_data.save()

    def test_index(self):
        response = self.client.get(reverse("chem_index"))
        self.assertEqual(response.status_code, 200)

    def test_index_redirect(self):
        for name in self.names + ["24{a,b}_TON"]:
            for keywords in ["opt HF/6-31g(d)", "td b3lyp/6-31g(d)", KEYWORDS]:
                params = "?molecule=%s&keywords=%s" % (name, keywords)
                url = reverse("chem_index") + params
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)

    def test_molecule_detail(self):
        for name in self.names:
            response = self.client.get(reverse(views.molecule_detail,
                                                args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_molecule_detail_invalid(self):
        for name in ["bad_name", "2nota_BEN"]:
            response = self.client.get(reverse(views.molecule_detail,
                                                args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_molecule_detail_json(self):
        for name in self.names:
            response = self.client.get(reverse(views.molecule_detail_json,
                                                args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_multi_molecule(self):
        names = ','.join(self.names)
        response = self.client.get(reverse(views.multi_molecule,
                                            args=(names, )))
        self.assertEqual(response.status_code, 200)

        options = self.options.copy()
        options["molname"] = "24a_TON"
        url = reverse(views.multi_molecule, args=(names, ))
        encoded_options = "?" + urllib.urlencode(options)
        response = self.client.get(url + encoded_options)
        self.assertEqual(response.status_code, 200)
        string = "{molname} {email} {nodes} {walltime}:00:00 {allocation}"
        self.assertEqual(response.content, string.format(**options))

    def test_multi_molecule_zip(self):
        names = ",".join(self.names)
        gjfnames = set([name + ".gjf" for name in self.names])
        response = self.client.get(reverse(views.multi_molecule_zip,
                                            args=(names, )))
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

        pairs = zip(["gjf", "image", "mol2"], [''] * 3)
        for group in itertools.product(*pairs):
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

    def test_multi_molecule_zip_job(self):
        options = self.options.copy()
        names = ",".join(self.names)
        jobnames = set([name + ".job" for name in self.names])
        url = reverse(views.multi_molecule_zip, args=(names, ))
        encoded_options = "?" + urllib.urlencode(options)
        response = self.client.get(url + encoded_options)

        string = "{name} {email} {nodes} {walltime}:00:00 {allocation}"
        self.assertEqual(response.status_code, 200)
        with StringIO(response.content) as f:
            with zipfile.ZipFile(f, "r") as zf:
                self.assertEqual(set(zf.namelist()), jobnames)
                for name in [x for x in zf.namelist() if not x.endswith("/")]:
                    with zf.open(name) as f2:
                        options["name"] = name.strip(".job")
                        self.assertEqual(f2.read(), string.format(**options))

    def test_multi_molecule_zip_job_bad(self):
        options = self.options.copy()
        options["email"] = "test.com"
        names = ",".join(self.names)
        jobnames = set([name + ".job" for name in self.names])
        url = reverse(views.multi_molecule_zip, args=(names, ))
        encoded_options = '?' + urllib.urlencode(options)
        response = self.client.get(url + encoded_options)
        self.assertEqual(response.status_code, 200)
        self.assertIn("has-error", response.content)

    def test_write_gjf(self):
        string = "%%nprocshared=16\n%%mem=59GB\n%%chk=%s.chk"
        string += "\n# opt B3LYP/6-31g(d) geom=connectivity"
        for name in self.names:
            response = self.client.get(reverse(views.write_gjf, args=(name, )))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get('Content-Disposition'),
                "attachment; filename=%s.gjf" % name)
            self.assertTrue(response.content.startswith(string % name))

    def test_write_gjf_keywords(self):
        string = "%%nprocshared=16\n%%mem=59GB\n"
        string += "%%chk=%s.chk\n# %s geom=connectivity"
        for name in self.names:
            for keywords in ["opt HF/6-31g(d)", "td b3lyp/6-31g(d)"]:
                params = "?keywords=%s" % keywords
                url = reverse(views.write_gjf, args=(name, )) + params
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.get('Content-Disposition'),
                    "attachment; filename=%s.gjf" % name)
                temp_string = string % (name, keywords)
                self.assertTrue(response.content.startswith(temp_string))

    def test_write_mol2(self):
        for name in self.names:
            response = self.client.get(reverse(views.write_mol2,
                                            args=(name, )))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get('Content-Disposition'),
                "attachment; filename=%s.mol2" % name)
            string = "@<TRIPOS>MOLECULE"
            self.assertTrue(response.content.startswith(string))

    def test_write_png(self):
        for name in self.names:
            response = self.client.get(reverse(views.write_png,
                                            args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_write_job(self):
        options = self.options.copy()
        del options["job"]
        del options["name"]
        for name in self.names:
            options["name"] = name
            response = self.client.get(reverse(views.molecule_detail,
                                            args=(name, )))
            self.assertEqual(response.status_code, 200)
            url = reverse(views.molecule_detail, args=(name, ))
            encoded_options = '?' + urllib.urlencode(options)
            response = self.client.get(url + encoded_options)
            self.assertEqual(response.status_code, 200)
            string = "{name} {email} {nodes} {walltime}:00:00 {allocation}"
            self.assertEqual(response.content, string.format(**options))

    def test_write_job_after_login(self):
        options = self.options.copy()
        del options["email"]
        del options["job"]
        del options["name"]

        for name in self.names:
            r = self.client.login(username=self.user["username"],
                                password=self.user["password"])
            self.assertTrue(r)

            options["name"] = name
            options["email"] = self.user["email"]
            response = self.client.get(reverse(views.molecule_detail,
                                                args=(name, )))
            self.assertEqual(response.status_code, 200)
            url = reverse(views.molecule_detail, args=(name, ))
            encoded_options = "?" + urllib.urlencode(options)
            response = self.client.get(url + encoded_options)
            self.assertEqual(response.status_code, 200)
            string = "{name} {email} {nodes} {walltime}:00:00 {allocation}"
            self.assertEqual(response.content, string.format(**options))

    def test_multi_job(self):
        response = self.client.get(reverse(views.multi_job))
        self.assertEqual(response.status_code, 200)

        options = self.options.copy()
        options["filenames"] = '\n'.join(self.names)
        del options["job"]

        url = reverse(views.multi_job) + '?' + urllib.urlencode(options)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        string = "{name} {email} {nodes} {walltime}:00:00 {allocation}"
        with StringIO(response.content) as f:
            with zipfile.ZipFile(f, "r") as zf:
                for name in [x for x in zf.namelist() if not x.endswith("/")]:
                    with zf.open(name) as f2:
                        d = options.copy()
                        d["name"] = name.split('.')[0]
                        self.assertEqual(f2.read(), string.format(**d))
                names = set([x + ".gjob" for x in self.names])
                self.assertEqual(set(zf.namelist()), names)

    def test_molecule_check(self):
        for name in self.names:
            response = self.client.get(reverse(views.molecule_check,
                                            args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_molecule_check_timeout(self):
        string = "{$ARYL2}{$RGROUPS}{$RGROUPS}{$XGROUPS}_TON"
        response = self.client.get(reverse(views.molecule_check,
                                        args=(string, )))
        self.assertEqual(response.status_code, 200)
        value = simplejson.loads(response.content)["error"]
        self.assertEqual(value, "The operation timed out.")

    def test_multi_molecule_zip_timeout(self):
        string = "{$ARYL2}{$RGROUPS}{$RGROUPS}{$XGROUPS}_TON"
        response = self.client.get(reverse(views.multi_molecule_zip,
                                        args=(string, )))
        self.assertEqual(response.status_code, 200)
        self.assertIn("The operation timed out.", response.content)

    def test_molecule_check_specific(self):
        names = [
            ("24ball_TON", "no rgroups allowed"),
            ("AA_TON", "can not attach to end"),
            ("A_TOO", "(1, 'Bad Core Name')"),
        ]
        for name, error in names:
            response = self.client.get(reverse(views.molecule_check,
                                            args=(name, )))
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
                response = self.client.get(reverse(views.molecule_check,
                                                    args=(name, )))
                values = simplejson.loads(response.content)["molecules"]
                self.assertFalse(values[0][1])

                response = self.client.get(reverse(views.report,
                                                    args=(name, )))
                self.assertEqual(response.status_code, 200)

                response = self.client.post(reverse(views.report,
                                                    args=(name, )), data)
                self.assertEqual(response.status_code, 302)

                response = self.client.get(reverse(views.molecule_check,
                                                    args=(name, )))
                values = simplejson.loads(response.content)["molecules"]
                self.assertTrue(values[0][1])

                obj = ErrorReport.objects.get(molecule=name)
                obj.delete()

    def test_report_molecule_after_login(self):
        names = [
            "24242424242a_TON",
            "25252525252a_TON",
            "26262626262a_TON",
        ]
        data = {
            "message": "something something something something"
        }
        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)
        for name in names:
            data["email"] = self.user["email"]
            for i in xrange(3):
                data["urgency"] = i
                response = self.client.get(reverse(views.molecule_check,
                                                args=(name, )))
                values = simplejson.loads(response.content)["molecules"]
                self.assertFalse(values[0][1])

                response = self.client.post(reverse(views.report,
                                                args=(name, )), data)
                self.assertEqual(response.status_code, 302)

                response = self.client.get(reverse(views.molecule_check,
                                                args=(name, )))
                values = simplejson.loads(response.content)["molecules"]
                self.assertTrue(values[0][1])

                obj = ErrorReport.objects.get(molecule=name)
                obj.delete()


class PostsFailTestCase(TestCase):
    names = ["24a_TON", "24b_TSP_24a_24a", "CON_24a", "A_TON_A_A"]
    cluster = {
            "name": "test-machine",
            "hostname": "localhost",
            "port": 2222,
        }
    credential = {
        "username": "vagrant",
        "password": "vagrant",
        "password2": "vagrant",
        "use_password": True,
    }
    options = {
        "email": "test@test.com",
        "nodes": 1,
        "walltime": 48,
        "allocation": "TG-CHE120081",
        "cluster": 'g',
        "template":
            "{{ name }} {{ email }} {{ nodes }} {{ time }} {{ allocation }}",
        "credential": 1,
    }

    def setUp(self):
        self.client = Client()
        self.user = {
            "username": "user1",
            "email": "user1@test.com",
            "password": "mypass",
        }
        new_user = User.objects.create_user(self.user["username"],
                                            self.user["email"],
                                            self.user["password"])
        new_user.save()
        cluster = Cluster(
                        name=self.cluster["name"],
                        hostname=self.cluster["hostname"],
                        port=self.cluster["port"])
        cluster.save()
        self.cluster = cluster
        credential = Credential(
                                user=new_user,
                                cluster=cluster,
                                username=self.credential["username"],
                                password=self.credential["password"],
                                use_password=True)
        credential.save()
        self.credential = credential

    def test_post_single_perm_fail(self):
        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)
        options = self.options.copy()
        for name in self.names:
            options["name"] = name
            response = self.client.get(reverse(views.molecule_detail,
                                                args=(name, )))
            self.assertEqual(response.status_code, 200)
            url = reverse(views.molecule_detail, args=(name, ))
            response = self.client.post(url, options)
            expected = {
                        "cluster": "test-machine",
                        "error": "You must be a staff user to submit a job.",
                        "jobid": None
                        }
            self.assertEqual(simplejson.loads(response.content), expected)

    def test_post_multi_perm_fail(self):
        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)

        name = ','.join(self.names)
        options = self.options.copy()
        options["name"] = name
        response = self.client.get(reverse(views.multi_molecule,
                                        args=(name, )))
        self.assertEqual(response.status_code, 200)
        url = reverse(views.multi_molecule, args=(name, ))
        response = self.client.post(url, options)
        expected = {
                    "cluster": "test-machine",
                    "error": "You must be a staff user to submit a job.",
                    "failed": [],
                    "worked": []
                    }
        self.assertEqual(simplejson.loads(response.content), expected)

    def test_post_multi_job_perm_fail(self):
        files = []
        base = os.path.join(settings.MEDIA_ROOT, "tests")
        for filename in ["A_TON_A_A", "A_TON_A_A_TD"]:
            path = os.path.join(base, filename + ".gjf")
            files.append(open(path, 'r'))

        options = self.options.copy()
        options["myfiles"] = files
        options["name"] = "{{ name }}"
        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)
        response = self.client.get(reverse(views.multi_job))
        self.assertEqual(response.status_code, 200)
        url = reverse(views.multi_job)
        response = self.client.post(url, options)
        expected = {
                    "cluster": "test-machine",
                    "error": "You must be a staff user to submit a job.",
                    "failed": [],
                    "worked": []
                    }
        self.assertEqual(simplejson.loads(response.content), expected)


class PostsTestCase(TestCase):
    names = ["24a_TON", "24b_TSP_24a_24a", "CON_24a", "A_TON_A_A"]
    bad_names = [
        ("2a_TON_CC", "no rgroups allowed"),
        ("ASADA", "(1, 'Bad Core Name')"),
        ("TON_CC_CC", "can not attach to end"),
    ]
    cluster = {
            "name": "test-machine",
            "hostname": "localhost",
            "port": 2222,
        }
    credential = {
        "username": "vagrant",
        "password": "vagrant",
        "password2": "vagrant",
        "use_password": True,
    }
    options = {
        "email": "test@test.com",
        "nodes": 1,
        "walltime": 48,
        "allocation": "TG-CHE120081",
        "cluster": 'g',
        "template":
            "{{ name }} {{ email }} {{ nodes }} {{ time }} {{ allocation }}",
        "credential": 1,
    }
    user = {
        "username": "admin",
        "email": "admin@test.com",
        "password": "mypass",
    }

    def setUp(self):
        self.client = Client()
        new_user = User.objects.create_superuser(**self.user)
        new_user.save()
        cluster = Cluster(
                        name=self.cluster["name"],
                        hostname=self.cluster["hostname"],
                        port=self.cluster["port"])
        cluster.save()
        self.cluster = cluster
        credential = Credential(
                                user=new_user,
                                cluster=cluster,
                                username=self.credential["username"],
                                password=self.credential["password"],
                                use_password=True)
        credential.save()
        self.credential = credential

    def test_post_single(self):
        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)
        options = self.options.copy()
        for name in self.names:
            options["name"] = name
            response = self.client.get(reverse(views.molecule_detail,
                                                args=(name, )))
            self.assertEqual(response.status_code, 200)
            url = reverse(views.molecule_detail, args=(name, ))
            response = self.client.post(url, options)

            results = simplejson.loads(response.content)
            self.assertIsNone(results["error"])
            self.assertIsNotNone(results["jobid"])

    def test_post_single_fail(self):
        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)
        options = self.options.copy()
        for name, error in self.bad_names:
            options["name"] = name
            response = self.client.get(reverse(views.molecule_detail,
                                                args=(name, )))
            self.assertEqual(response.status_code, 200)
            url = reverse(views.molecule_detail, args=(name, ))
            response = self.client.post(url, options)

            results = simplejson.loads(response.content)
            self.assertEqual(results["error"], error)
            self.assertIsNone(results["jobid"])

    def test_post_multi(self):
        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)

        name = ','.join(self.names)
        options = self.options.copy()
        options["name"] = "{{ name }}"
        response = self.client.get(reverse(views.multi_molecule,
                                        args=(name, )))
        self.assertEqual(response.status_code, 200)
        url = reverse(views.multi_molecule, args=(name, ))
        response = self.client.post(url, options)

        results = simplejson.loads(response.content)
        self.assertIsNone(results["error"])
        self.assertEqual(len(results["worked"]), len(self.names))
        self.assertEqual(len(results["failed"]), 0)

    def test_post_multi_fail(self):
        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)

        names, errors = zip(*self.bad_names)
        string = ','.join(names)
        options = self.options.copy()
        options["name"] = "{{ name }}"
        response = self.client.get(reverse(views.multi_molecule,
                                        args=(string, )))
        self.assertEqual(response.status_code, 200)
        url = reverse(views.multi_molecule, args=(string, ))
        response = self.client.post(url, options)

        results = simplejson.loads(response.content)
        self.assertIsNone(results["error"])
        self.assertEqual(len(results["worked"]), 0)
        self.assertEqual(len(results["failed"]), len(names))

    def test_post_multi_job(self):
        files = []
        base = os.path.join(settings.MEDIA_ROOT, "tests")
        for filename in ["A_TON_A_A", "A_TON_A_A_TD"]:
            path = os.path.join(base, filename + ".gjf")
            files.append(open(path, 'r'))

        options = self.options.copy()
        options["files"] = files
        options["name"] = "{{ name }}"
        r = self.client.login(username=self.user["username"],
                            password=self.user["password"])
        self.assertTrue(r)
        response = self.client.get(reverse(views.multi_job))
        self.assertEqual(response.status_code, 200)
        url = reverse(views.multi_job)
        response = self.client.post(url, options)

        results = simplejson.loads(response.content)
        self.assertIsNone(results["error"])
        self.assertEqual(len(results["worked"]), len(files))
        self.assertEqual(len(results["failed"]), 0)
