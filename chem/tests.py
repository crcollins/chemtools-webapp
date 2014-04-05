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
import utils

from models import ErrorReport


NAMES = ["24a_TON", "24b_TSP_24a_24a", "CON_24a", "A_TON_A_A", "TON_CCC"]
BAD_NAMES = [
        ("2a_TON_CC", "no rgroups allowed"),
        ("ASADA", "(1, 'Bad Core Name')"),
        ("TON_CC_CC", "can not attach to end"),
]
TEST_NAMES = ["A_TON_A_A", "A_TON_A_A_TD"]
MULTI_NAMES = ["24{a,b}_TON"]
WARN_NAMES = [
            "24242424242a_TON",
            "25252525252a_TON",
            "26262626262a_TON",
]
OPTIONS = {
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
DATA_POINT = {
            "name": "A_TON_A_A",
            "exact_name": "A_TON_A_A_n1_m1_x1_y1_z1",
            "options": "td B3LYP/6-31g(d) geom=connectivity",
            "homo": -6.460873931,
            "lumo": -1.31976745,
            "homo_orbital": 41,
            "dipole": 0.0006,
            "energy": -567.1965205,
            "band_gap": 4.8068,
}
USER = {
    "username": "user1",
    "email": "user1@test.com",
    "password": "mypass",
}
USER_LOGIN = USER.copy()
del USER_LOGIN["email"]

JOB_STRING = "{name} {email} {nodes} {walltime}:00:00 {allocation}"
TIMEOUT_NAMES = "{$ARYL2}{$RGROUPS}{$RGROUPS}{$XGROUPS}_TON"

CLUSTER = {
        "name": "test-machine",
        "hostname": "localhost",
        "port": 2222,
}
CREDENTIAL = {
    "username": "vagrant",
    "password": "vagrant",
    "use_password": True,
}

SUB_OPTIONS = {
    "email": "test@test.com",
    "nodes": 1,
    "walltime": 48,
    "allocation": "TG-CHE120081",
    "cluster": 'g',
    "template":
        "{{ name }} {{ email }} {{ nodes }} {{ time }} {{ allocation }}",
    "credential": 1,
}

KEYWORDS_SET = ["opt HF/6-31g(d)", "td b3lyp/6-31g(d)", KEYWORDS]


class MainPageTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        new_user = User.objects.create_user(**USER)
        new_user.save()
        new_data = DataPoint(**DATA_POINT)
        new_data.save()

    def test_index(self):
        response = self.client.get(reverse("chem_index"))
        self.assertEqual(response.status_code, 200)

    def test_index_redirect(self):
        for name in NAMES + MULTI_NAMES:
            for keywords in KEYWORDS_SET:
                params = "?molecule=%s&keywords=%s" % (name, keywords)
                url = reverse("chem_index") + params
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)

    def test_molecule_detail(self):
        for name in NAMES:
            response = self.client.get(reverse(views.molecule_detail,
                                                args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_molecule_detail_invalid(self):
        for name, reason in BAD_NAMES:
            response = self.client.get(reverse(views.molecule_detail,
                                                args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_molecule_detail_json(self):
        for name in NAMES:
            response = self.client.get(reverse(views.molecule_detail_json,
                                                args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_multi_molecule(self):
        string = ','.join(NAMES)
        response = self.client.get(reverse(views.multi_molecule,
                                            args=(string, )))
        self.assertEqual(response.status_code, 200)

        options = OPTIONS.copy()
        options["molname"] = NAMES[0]
        url = reverse(views.multi_molecule, args=(string, ))
        encoded_options = "?" + urllib.urlencode(options)
        response = self.client.get(url + encoded_options)
        self.assertEqual(response.status_code, 200)
        options["name"] = NAMES[0]
        self.assertEqual(response.content, JOB_STRING.format(**options))

    def test_multi_molecule_zip(self):
        string = ','.join(NAMES)
        gjf_names = set([name + ".gjf" for name in NAMES])
        response = self.client.get(reverse(views.multi_molecule_zip,
                                            args=(string, )))
        self.assertEqual(response.status_code, 200)
        with StringIO(response.content) as f:
            with zipfile.ZipFile(f, "r") as zfile:
                self.assertEqual(set(zfile.namelist()), gjf_names)

    def test_multi_molecule_zip_keywords(self):
        string = ','.join(NAMES)
        gjf_names = set([name + ".gjf" for name in NAMES])
        header = "%%nprocshared=16\n%%mem=59GB\n"
        header += "%%chk=%s.chk\n# %s geom=connectivity"

        for keywords in KEYWORDS_SET:
            params = "?keywords=%s" % keywords
            url = reverse(views.multi_molecule_zip, args=(string, )) + params
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

            with StringIO(response.content) as f:
                with zipfile.ZipFile(f, "r") as zfile:
                    for gjf_name in zfile.namelist():
                        with zfile.open(gjf_name) as f1:
                            name = gjf_name.replace(".gjf", '')
                            temp_string = header % (name, keywords)
                            t = [x + '\n' for x in temp_string.split('\n')]
                            self.assertEqual(t, f1.readlines()[:4])

    def test_multi_molecule_zip_unique(self):
        string = ','.join(NAMES)
        exists = DATA_POINT["name"]
        gjf_names = set([name + ".gjf" for name in NAMES if name != exists])
        url = reverse(views.multi_molecule_zip, args=(string, ))
        params = "?unique=true"
        response = self.client.get(url + params)
        self.assertEqual(response.status_code, 200)
        with StringIO(response.content) as f:
            with zipfile.ZipFile(f, "r") as zfile:
                self.assertEqual(set(zfile.namelist()), gjf_names)

    def test_multi_molecule_zip_options(self):
        string = ','.join(NAMES)
        sets = {
            "gjf": set([name + ".gjf" for name in NAMES]),
            "image": set([name + ".png" for name in NAMES]),
            "mol2": set([name + ".mol2" for name in NAMES]),
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
            url = reverse(views.multi_molecule_zip, args=(string, )) + params

            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            with StringIO(response.content) as f:
                with zipfile.ZipFile(f, "r") as zfile:
                    self.assertEqual(set(zfile.namelist()), comparenames)

    def test_multi_molecule_zip_options_unique(self):
        string = ','.join(NAMES)
        exists = DATA_POINT["name"]
        sets = {
            "gjf": set([name + ".gjf" for name in NAMES if name != exists]),
            "image": set([name + ".png" for name in NAMES if name != exists]),
            "mol2": set([name + ".mol2" for name in NAMES if name != exists]),
            "": set(),
        }

        pairs = zip(["gjf", "image", "mol2"], [''] * 3)
        for group in itertools.product(*pairs):
            params = '?' + '&'.join([x + "=true" for x in group if x])
            if params == '?':  # remove the blank case
                continue
            params += "&unique=true"
            comparenames = set()
            for x in group:
                comparenames |= sets[x]
            url = reverse(views.multi_molecule_zip, args=(string, )) + params

            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            with StringIO(response.content) as f:
                with zipfile.ZipFile(f, "r") as zfile:
                    self.assertEqual(set(zfile.namelist()), comparenames)

    def test_multi_molecule_zip_job(self):
        options = OPTIONS.copy()
        string = ','.join(NAMES)
        jobnames = set([name + ".job" for name in NAMES])
        url = reverse(views.multi_molecule_zip, args=(string, ))
        encoded_options = "?" + urllib.urlencode(options)
        response = self.client.get(url + encoded_options)

        self.assertEqual(response.status_code, 200)
        with StringIO(response.content) as f:
            with zipfile.ZipFile(f, "r") as zf:
                self.assertEqual(set(zf.namelist()), jobnames)
                for name in [x for x in zf.namelist() if not x.endswith("/")]:
                    with zf.open(name) as f2:
                        options["name"] = name.strip(".job")
                        temp_string = JOB_STRING.format(**options)
                        self.assertEqual(f2.read(), temp_string)

    def test_multi_molecule_zip_job_bad(self):
        options = OPTIONS.copy()
        options["email"] = "test.com"
        names = ','.join(NAMES)
        jobnames = set([name + ".job" for name in NAMES])
        url = reverse(views.multi_molecule_zip, args=(names, ))
        encoded_options = '?' + urllib.urlencode(options)
        response = self.client.get(url + encoded_options)
        self.assertEqual(response.status_code, 200)
        self.assertIn("has-error", response.content)

    def test_write_gjf(self):
        string = "%%nprocshared=16\n%%mem=59GB\n%%chk=%s.chk"
        string += "\n# opt B3LYP/6-31g(d) geom=connectivity"
        for name in NAMES:
            response = self.client.get(reverse(views.write_gjf, args=(name, )))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get('Content-Disposition'),
                "attachment; filename=%s.gjf" % name)
            self.assertTrue(response.content.startswith(string % name))

    def test_write_gjf_keywords(self):
        string = "%%nprocshared=16\n%%mem=59GB\n"
        string += "%%chk=%s.chk\n# %s geom=connectivity"
        for name in NAMES:
            for keywords in KEYWORDS_SET:
                params = "?keywords=%s" % keywords
                url = reverse(views.write_gjf, args=(name, )) + params
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.get('Content-Disposition'),
                    "attachment; filename=%s.gjf" % name)
                temp_string = string % (name, keywords)
                self.assertTrue(response.content.startswith(temp_string))

    def test_write_mol2(self):
        for name in NAMES:
            response = self.client.get(reverse(views.write_mol2,
                                            args=(name, )))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get('Content-Disposition'),
                "attachment; filename=%s.mol2" % name)
            string = "@<TRIPOS>MOLECULE"
            self.assertTrue(response.content.startswith(string))

    def test_write_png(self):
        for name in NAMES:
            response = self.client.get(reverse(views.write_png,
                                            args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_write_job(self):
        options = OPTIONS.copy()
        del options["job"]
        del options["name"]
        for name in NAMES:
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
        options = OPTIONS.copy()
        del options["email"]
        del options["job"]
        del options["name"]

        for name in NAMES:
            r = self.client.login(**USER_LOGIN)
            self.assertTrue(r)

            options["name"] = name
            options["email"] = USER["email"]
            response = self.client.get(reverse(views.molecule_detail,
                                                args=(name, )))
            self.assertEqual(response.status_code, 200)
            url = reverse(views.molecule_detail, args=(name, ))
            encoded_options = "?" + urllib.urlencode(options)
            response = self.client.get(url + encoded_options)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, JOB_STRING.format(**options))

    def test_multi_job(self):
        response = self.client.get(reverse(views.multi_job))
        self.assertEqual(response.status_code, 200)

        options = OPTIONS.copy()
        options["filenames"] = '\n'.join(NAMES)
        del options["job"]

        url = reverse(views.multi_job) + '?' + urllib.urlencode(options)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        with StringIO(response.content) as f:
            with zipfile.ZipFile(f, "r") as zf:
                for name in [x for x in zf.namelist() if not x.endswith("/")]:
                    with zf.open(name) as f2:
                        d = options.copy()
                        d["name"] = name.split('.')[0]
                        self.assertEqual(f2.read(), JOB_STRING.format(**d))
                names = set([x + ".gjob" for x in NAMES])
                self.assertEqual(set(zf.namelist()), names)

    def test_molecule_check(self):
        for name in NAMES:
            response = self.client.get(reverse(views.molecule_check,
                                            args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_molecule_check_timeout(self):
        response = self.client.get(reverse(views.molecule_check,
                                        args=(TIMEOUT_NAMES, )))
        self.assertEqual(response.status_code, 200)
        value = simplejson.loads(response.content)["error"]
        self.assertEqual(value, "The operation has timed out.")

    def test_multi_molecule_zip_timeout(self):
        response = self.client.get(reverse(views.multi_molecule_zip,
                                        args=(TIMEOUT_NAMES, )))
        self.assertEqual(response.status_code, 200)
        self.assertIn("The operation has timed out.", response.content)

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
        data = {
            "email": "something@test.com",
            "message": "something something something something"
        }
        for i, name in enumerate(WARN_NAMES):
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


    def test_report_molecule_after_login(self):
        data = {
            "message": "something something something something"
        }
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)
        for i, name in enumerate(WARN_NAMES):
            data["email"] = USER["email"]
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

    def test_report_molecule_invalid(self):
        data = {
            "email": "bademail.com",
            "message": "something something something something"
        }
        for i, name in enumerate(WARN_NAMES):
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
            self.assertEqual(response.status_code, 200)
            self.assertIn("Enter a valid e-mail", response.content)


class PostsFailTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        new_user = User.objects.create_user(**USER)
        new_user.save()
        cluster = Cluster(**CLUSTER)
        cluster.save()
        self.cluster = cluster
        credential = Credential(user=new_user,
                                cluster=cluster,
                                **CREDENTIAL)
        credential.save()
        self.credential = credential

    def test_post_single_perm_fail(self):
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)
        options = SUB_OPTIONS.copy()
        for name in NAMES:
            options["name"] = name
            response = self.client.get(reverse(views.molecule_detail,
                                                args=(name, )))
            self.assertEqual(response.status_code, 200)
            url = reverse(views.molecule_detail, args=(name, ))
            response = self.client.post(url, options)
            expected = {
                        "cluster": "test-machine",
                        "error": "You must be a staff user to submit a job.",
                        "jobid": None,
                        'success': True
                        }
            self.assertEqual(simplejson.loads(response.content), expected)

    def test_post_multi_perm_fail(self):
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)

        string = ','.join(NAMES)
        options = SUB_OPTIONS.copy()
        options["name"] = string
        response = self.client.get(reverse(views.multi_molecule,
                                        args=(string, )))
        self.assertEqual(response.status_code, 200)
        url = reverse(views.multi_molecule, args=(string, ))
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
        for filename in TEST_NAMES:
            path = os.path.join(base, filename + ".gjf")
            files.append(open(path, 'r'))

        options = SUB_OPTIONS.copy()
        options["myfiles"] = files
        options["name"] = "{{ name }}"
        r = self.client.login(**USER_LOGIN)
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

    def setUp(self):
        self.client = Client()
        new_user = User.objects.create_superuser(**USER)
        new_user.save()
        cluster = Cluster(**CLUSTER)
        cluster.save()
        self.cluster = cluster
        credential = Credential(
                                user=new_user,
                                cluster=cluster,
                                **CREDENTIAL)
        credential.save()
        self.credential = credential

    def test_post_single(self):
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)
        options = SUB_OPTIONS.copy()
        for name in NAMES:
            options["name"] = name
            response = self.client.get(reverse(views.molecule_detail,
                                                args=(name, )))
            self.assertEqual(response.status_code, 200)
            url = reverse(views.molecule_detail, args=(name, ))
            response = self.client.post(url, options)

            results = simplejson.loads(response.content)
            self.assertIsNone(results["error"])
            self.assertIsNotNone(results["jobid"])

    def test_post_single_exception(self):
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)
        options = SUB_OPTIONS.copy()
        for name in NAMES:
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
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)
        options = SUB_OPTIONS.copy()
        for name, error in BAD_NAMES:
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
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)

        name = ','.join(NAMES)
        options = SUB_OPTIONS.copy()
        options["name"] = "{{ name }}"
        response = self.client.get(reverse(views.multi_molecule,
                                        args=(name, )))
        self.assertEqual(response.status_code, 200)
        url = reverse(views.multi_molecule, args=(name, ))
        response = self.client.post(url, options)

        results = simplejson.loads(response.content)
        self.assertIsNone(results["error"])
        self.assertEqual(len(results["worked"]), len(NAMES))
        self.assertEqual(len(results["failed"]), 0)

    def test_post_multi_fail(self):
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)

        names, errors = zip(*BAD_NAMES)
        string = ','.join(names)
        options = SUB_OPTIONS.copy()
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
        for filename in TEST_NAMES:
            path = os.path.join(base, filename + ".gjf")
            files.append(open(path, 'r'))

        options = SUB_OPTIONS.copy()
        options["files"] = files
        options["name"] = "{{ name }}"
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)
        response = self.client.get(reverse(views.multi_job))
        self.assertEqual(response.status_code, 200)
        url = reverse(views.multi_job)
        response = self.client.post(url, options)

        results = simplejson.loads(response.content)
        self.assertIsNone(results["error"])
        self.assertEqual(len(results["worked"]), len(files))
        self.assertEqual(len(results["failed"]), 0)


class UtilsTestCase(TestCase):
    names = ["24a_TON", "BAD_NAME", "CON_24a", "A_TON_A_A"]

    def setUp(self):
        new_data = DataPoint(**DATA_POINT)
        new_data.save()
        new_error = ErrorReport(molecule="CON_24a",
                                email="test@test.com",
                                urgency=1,
                                message="This is a message")
        new_error.save()

    def test_get_multi_molecule_warnings(self):
        string = ','.join(self.names)
        results = utils.get_multi_molecule_warnings(string)
        expected = (
                    self.names,
                    [None, None, True, None],
                    [None, "(1, 'Bad Core Name')", None, None],
                    [True, True, True, False],
                )
        self.assertEqual(results, expected)

    def test_get_multi_molecule_warnings_unique(self):
        string = ','.join(self.names)
        results = utils.get_multi_molecule_warnings(string)
        expected = (
                    self.names,
                    [None, None, True, None],
                    [None, "(1, 'Bad Core Name')", None, None],
                    [True, True, True, False]
                )
        self.assertEqual(results, expected)

    def test_get_molecule_info(self):
        name = "24a_TON"
        results = utils.get_molecule_info(name)
        del results["features"]
        expected = {
            'molecule': '24a_TON',
            'lumo': -1.8018644353251334,
            'homo': -6.0349352189700411,
            'exact_name': '24aaA_TON_A_A_n1_m1_x1_y1_z1',
            'keywords': 'opt B3LYP/6-31g(d)',
            'band_gap': 3.9119664787437074,
            'limits': {
                'm': [
                    -5.7791157248205742,
                    -2.3610428502402536,
                    2.8213594294564546],
                'n': [
                    -5.7347154609610094,
                    -3.3180621721837378,
                    1.8808350405523875]
                },
            'known_errors': None,
            'error_message': None,
            'datapoint': None,
            'unique': True,
            'exact_name_spacers': '2**4aaA**_TON_A**_A**_n1_m1_x1_y1_z1'
        }
        self.assertEqual(results, expected)

