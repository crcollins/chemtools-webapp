import os
import csv
import zipfile
import itertools
import urllib
from unittest import skipUnless

from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.contrib.auth.models import User
from django.conf import settings

from project.utils import StringIO, server_exists
from data.models import DataPoint
from cluster.models import Cluster, Credential
from chemtools.constants import KEYWORDS
import views
import utils

from models import ErrorReport


NAMES = ["24a_TON", "24b_TSP_24a_24a", "CON_24a", "A_TON_A_A", "TON_CCC"]
BAD_NAMES = [
        ("2a_TON_CC", "no rgroups allowed on aryl0"),
        ("ASADA", "Bad Substituent Name(s): [u'S']"),
        ("TON_CC_CC", "'C' can not attach to end"),
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

SUPER_USER = {
    "username": "user",
    "email": "user@test.com",
    "password": "mypass",
}
SUPER_USER_LOGIN = SUPER_USER.copy()
del SUPER_USER_LOGIN["email"]

JOB_STRING = "{name} {email} {nodes} {walltime}:00:00 {allocation}"
TIMEOUT_NAMES = "{$ARYL2}{$RGROUPS}{$RGROUPS}{$XGROUPS}_TON"

CLUSTER = {
    "name": "test-machine",
    "hostname": "localhost",
    "port": 2222,
}
SERVER = {
    "hostname": "localhost",
    "port": 2222,
    "username": "vagrant",
    "password": "vagrant",
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
    "template":
        "{{ name }} {{ email }} {{ nodes }} {{ time }} {{ allocation }}",
    "credential": 1,
}
SUB_OPTIONS2 = SUB_OPTIONS.copy()
SUB_OPTIONS2["credential"] = 2

KEYWORDS_SET = ["opt HF/6-31g(d)", "td b3lyp/6-31g(d)", KEYWORDS]
SUBMIT_ERROR = "You must be a staff user to submit a job."
CRED_ERROR = "Invalid credential"


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

    def test_multi_molecule_zip_new(self):
        string = ','.join(NAMES)
        exists = DATA_POINT["name"]
        gjf_names = set([name + ".gjf" for name in NAMES if name != exists])
        url = reverse(views.multi_molecule_zip, args=(string, ))
        params = "?new=true"
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

    def test_multi_molecule_zip_options_new(self):
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
            params += "&new=true"
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

    def test_write_svg(self):
        for name in NAMES:
            response = self.client.get(reverse(views.write_svg,
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
                names = set([x + ".job" for x in NAMES])
                self.assertEqual(set(zf.namelist()), names)

    def test_molecule_check(self):
        for name in NAMES:
            response = self.client.get(reverse(views.molecule_check,
                                            args=(name, )))
            self.assertEqual(response.status_code, 200)

    def test_molecule_check_html(self):
        for name in NAMES:
            url = reverse(views.molecule_check, args=(name, )) + "?html=true"
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertIn("<tbody>", response.content)

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
            ("24ball_TON", "no rgroups allowed at start"),
            ("AA_TON", "'A' can not attach to end"),
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
        norm_user = User.objects.create_user(**USER)
        norm_user.save()
        super_user = User.objects.create_superuser(**SUPER_USER)
        super_user.save()
        cluster = Cluster(**CLUSTER)
        cluster.save()
        self.cluster = cluster
        credential = Credential(user=norm_user,
                                cluster=cluster,
                                **CREDENTIAL)
        credential.save()
        credential = Credential(user=super_user,
                                cluster=cluster,
                                **CREDENTIAL)
        credential.save()
        self.credential = credential

    def test_post_single_fail(self):
        r = self.client.login(**SUPER_USER_LOGIN)
        self.assertTrue(r)

        options = SUB_OPTIONS2.copy()
        for name, error in BAD_NAMES:
            options["name"] = name
            response = self.client.get(reverse(views.molecule_detail,
                                                args=(name, )))
            self.assertEqual(response.status_code, 200)
            url = reverse(views.molecule_detail, args=(name, ))
            response = self.client.post(url, options)

            results = simplejson.loads(response.content)
            self.assertEqual(results["failed"][0][1], error)
            self.assertFalse(len(results['worked']) > 0)

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
                        "failed": [],
                        "worked": [],
                        }
            self.assertEqual(simplejson.loads(response.content), expected)

    def test_post_single_ajax_fail(self):
        r = self.client.login(**SUPER_USER_LOGIN)
        self.assertTrue(r)
        options = SUB_OPTIONS2.copy()
        for name, error in BAD_NAMES:
            options["name"] = name
            options["email"] = ""
            response = self.client.get(reverse(views.molecule_detail,
                                                args=(name, )))
            self.assertEqual(response.status_code, 200)
            url = reverse(views.molecule_detail, args=(name, ))
            response = self.client.post(url, options,
                                        HTTP_X_REQUESTED_WITH="XMLHttpRequest")
            results = simplejson.loads(response.content)
            self.assertFalse(results["success"])
            self.assertIn("has-error", results["job_form_html"])

    def test_post_single_ajax_fail_template(self):
        r = self.client.login(**SUPER_USER_LOGIN)
        self.assertTrue(r)
        options = SUB_OPTIONS2.copy()
        for name, error in BAD_NAMES:
            options["name"] = name
            options["template"] = ""
            options["base_template"] = None
            response = self.client.get(reverse(views.molecule_detail,
                                                args=(name, )))
            self.assertEqual(response.status_code, 200)
            url = reverse(views.molecule_detail, args=(name, ))
            response = self.client.post(url, options,
                                        HTTP_X_REQUESTED_WITH="XMLHttpRequest")
            results = simplejson.loads(response.content)
            self.assertFalse(results["success"])
            message = "A template or base template is required."
            self.assertIn(message, results["job_form_html"])

    def test_post_multi_fail(self):
        r = self.client.login(**SUPER_USER_LOGIN)
        self.assertTrue(r)

        names, errors = zip(*BAD_NAMES)
        string = ','.join(names)
        options = SUB_OPTIONS2.copy()
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

    def test_post_multi_ajax_fail(self):
        r = self.client.login(**SUPER_USER_LOGIN)
        self.assertTrue(r)

        name = ','.join(NAMES)
        options = SUB_OPTIONS2.copy()
        options["name"] = "{{ name }}"
        options["email"] = ''
        response = self.client.get(reverse(views.multi_molecule,
                                        args=(name, )))
        self.assertEqual(response.status_code, 200)
        url = reverse(views.multi_molecule, args=(name, ))
        response = self.client.post(url, options,
                                    HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        results = simplejson.loads(response.content)
        self.assertFalse(results["success"])
        self.assertIn("has-error", results["job_form_html"])

    def test_post_multi_job_perm_fail(self):
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)

        files = []
        base = os.path.join(settings.MEDIA_ROOT, "tests")
        for filename in TEST_NAMES:
            path = os.path.join(base, filename + ".gjf")
            files.append(open(path, 'r'))

        options = SUB_OPTIONS.copy()
        options["myfiles"] = files
        options["name"] = "{{ name }}"
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

    def test_post_multi_job_ajax_fail(self):
        r = self.client.login(**SUPER_USER_LOGIN)
        self.assertTrue(r)

        files = []
        base = os.path.join(settings.MEDIA_ROOT, "tests")
        for filename in TEST_NAMES:
            path = os.path.join(base, filename + ".gjf")
            files.append(open(path, 'r'))

        options = SUB_OPTIONS2.copy()
        options["files"] = files
        options["name"] = "{{ name }}"
        options["email"] = ""
        response = self.client.get(reverse(views.multi_job))
        self.assertEqual(response.status_code, 200)
        url = reverse(views.multi_job)
        response = self.client.post(url, options,
                                    HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        results = simplejson.loads(response.content)
        self.assertFalse(results["success"])
        self.assertIn("has-error", results["job_form_html"])

    def test_gjf_reset_submit_fail(self):
        r = self.client.login(**SUPER_USER_LOGIN)
        self.assertTrue(r)

        base = os.path.join(settings.MEDIA_ROOT, "tests", "A_TON_A_A")
        log_path = base + ".log"
        with open(log_path, 'r') as log:
            temp = {
                "files": log,
                "options": "gjfreset",
                "gjf_submit": True,
                "name": "{{ name }}",
            }
            data = dict(temp.items() + SUB_OPTIONS2.items())
            del data["email"]
            response = self.client.post(reverse(views.upload_data), data)
            self.assertEqual(response.status_code, 200)

    def test_gjf_reset_submit_ajax_fail(self):
        r = self.client.login(**SUPER_USER_LOGIN)
        self.assertTrue(r)

        base = os.path.join(settings.MEDIA_ROOT, "tests", "A_TON_A_A")
        log_path = base + ".log"
        with open(log_path, 'r') as log:
            temp = {
                "files": log,
                "options": "gjfreset",
                "gjf_submit": True,
                "name": "{{ name }}",
            }
            data = dict(temp.items() + SUB_OPTIONS2.items())
            del data["email"]
            response = self.client.post(reverse(views.upload_data), data,
                                        HTTP_X_REQUESTED_WITH="XMLHttpRequest")
            self.assertEqual(response.status_code, 200)
            value = simplejson.loads(response.content)
            self.assertFalse(value['success'])
            self.assertIn("has-error", value["job_form_html"])


@skipUnless(server_exists(**SERVER), "Requires external test server.")
class PostsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        new_user = User.objects.create_superuser(**SUPER_USER)
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
        r = self.client.login(**SUPER_USER_LOGIN)
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
            self.assertTrue(len(results["worked"]))


    def test_post_multi(self):
        r = self.client.login(**SUPER_USER_LOGIN)
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

    def test_post_multi_html(self):
        r = self.client.login(**SUPER_USER_LOGIN)
        self.assertTrue(r)

        name = ','.join(NAMES)
        options = SUB_OPTIONS.copy()
        options["name"] = "{{ name }}"
        options["html"] = True
        response = self.client.get(reverse(views.multi_molecule,
                                        args=(name, )))
        self.assertEqual(response.status_code, 200)
        url = reverse(views.multi_molecule, args=(name, ))
        response = self.client.post(url, options)

        results = simplejson.loads(response.content)
        self.assertTrue(results["success"])
        self.assertIn("Go to jobs list", response.content)

    def test_post_multi_job(self):
        r = self.client.login(**SUPER_USER_LOGIN)
        self.assertTrue(r)

        files = []
        base = os.path.join(settings.MEDIA_ROOT, "tests")
        for filename in TEST_NAMES:
            path = os.path.join(base, filename + ".gjf")
            files.append(open(path, 'r'))

        options = SUB_OPTIONS.copy()
        options["files"] = files
        options["name"] = "{{ name }}"
        response = self.client.get(reverse(views.multi_job))
        self.assertEqual(response.status_code, 200)
        url = reverse(views.multi_job)
        response = self.client.post(url, options)

        results = simplejson.loads(response.content)
        self.assertIsNone(results["error"])
        self.assertEqual(len(results["worked"]), len(files))
        self.assertEqual(len(results["failed"]), 0)

    def test_post_multi_job_html(self):
        r = self.client.login(**SUPER_USER_LOGIN)
        self.assertTrue(r)

        files = []
        base = os.path.join(settings.MEDIA_ROOT, "tests")
        for filename in TEST_NAMES:
            path = os.path.join(base, filename + ".gjf")
            files.append(open(path, 'r'))

        options = SUB_OPTIONS.copy()
        options["files"] = files
        options["name"] = "{{ name }}"
        options["html"] = True
        response = self.client.get(reverse(views.multi_job))
        self.assertEqual(response.status_code, 200)
        url = reverse(views.multi_job)
        response = self.client.post(url, options)

        results = simplejson.loads(response.content)
        self.assertTrue(results["success"])
        self.assertIn("Go to jobs list", response.content)

    def test_gjf_reset_submit(self):
        r = self.client.login(**SUPER_USER_LOGIN)
        self.assertTrue(r)

        base = os.path.join(settings.MEDIA_ROOT, "tests", "A_TON_A_A")
        log_path = base + ".log"
        with open(log_path, 'r') as log:
            temp = {
                "files": log,
                "options": "gjfreset",
                "gjf_submit": True,
                "name": "{{ name }}",
            }
            data = dict(temp.items() + SUB_OPTIONS.items())
            response = self.client.post(reverse(views.upload_data), data)
            self.assertEqual(response.status_code, 200)
            results = simplejson.loads(response.content)
            self.assertIsNone(results["error"])
            self.assertEqual(len(results["worked"]), 1)
            self.assertEqual(len(results["failed"]), 0)

    def test_gjf_reset_submit_td(self):
        r = self.client.login(**SUPER_USER_LOGIN)
        self.assertTrue(r)

        base = os.path.join(settings.MEDIA_ROOT, "tests", "A_TON_A_A")
        log_path = base + ".log"
        with open(log_path, 'r') as log:
            temp = {
                "files": log,
                "options": "gjfreset",
                "td_reset": True,
                "gjf_submit": True,
                "name": "{{ name }}",
            }
            data = dict(temp.items() + SUB_OPTIONS.items())
            response = self.client.post(reverse(views.upload_data), data)
            self.assertEqual(response.status_code, 200)
            results = simplejson.loads(response.content)
            self.assertIsNone(results["error"])
            self.assertEqual(len(results["worked"]), 1)
            self.assertEqual(len(results["failed"]), 0)

    def test_gjf_reset_submit_html(self):
        r = self.client.login(**SUPER_USER_LOGIN)
        self.assertTrue(r)

        base = os.path.join(settings.MEDIA_ROOT, "tests", "A_TON_A_A")
        log_path = base + ".log"
        with open(log_path, 'r') as log:
            temp = {
                "files": log,
                "options": "gjfreset",
                "gjf_submit": True,
                "html": True,
                "name": "{{ name }}",
            }
            data = dict(temp.items() + SUB_OPTIONS.items())
            response = self.client.post(reverse(views.upload_data), data)
            self.assertEqual(response.status_code, 200)
            results = simplejson.loads(response.content)
            self.assertTrue(results["success"])
            self.assertIn("Go to jobs list", response.content)




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
        expected = [
                    tuple(self.names),
                    (None, None, True, None),
                    (None, "Bad Substituent Name(s): ['_N']", None, None),
                    (True, True, True, False),
                ]
        self.assertEqual(results, expected)

    def test_get_multi_molecule_warnings_new(self):
        string = ','.join(self.names)
        results = utils.get_multi_molecule_warnings(string)
        expected = [
                    tuple(self.names),
                    (None, None, True, None),
                    (None, "Bad Substituent Name(s): ['_N']", None, None),
                    (True, True, True, False)
                ]
        self.assertEqual(results, expected)

    def test_get_molecule_info(self):
        name = "24a_TON"
        results = utils.get_molecule_info(name)
        del results["features"]
        expected = {
            'molecule': '24a_TON',
            'lumo': -2.1298787902985779,
            'homo': -5.6866366091077571,
            'exact_name': '24aaA_TON_A_A_n1_m1_x1_y1_z1',
            'band_gap': 3.4415766653971942,
            'limits': {
                'm': [
                    -5.5380175794413322,
                    -2.3145802963818163,
                    2.9191909229300554],
                'n': [
                    -5.74066757207639,
                    -2.9489392195479147,
                    2.5846925036411794]
                },
            'known_errors': None,
            'error_message': None,
            'datapoint': None,
            'new': True,
            'exact_name_spacers': '2**4aaA**_TON_A**_A**_n1_m1_x1_y1_z1'
        }
        self.assertEqual(results, expected)

    def test_StringIO_size(self):
        string = "some test string"
        s = StringIO(string)
        self.assertEqual(s.size, len(string))


@skipUnless(server_exists(**SERVER), "Requires external test server.")
class UtilsServerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(**USER)
        self.user.save()
        super_user = User.objects.create_superuser(**SUPER_USER)
        super_user.save()

        profile = self.user.get_profile()
        test_path = os.path.join(settings.MEDIA_ROOT, "tests")
        with open(os.path.join(test_path, "id_rsa.pub"), 'r') as f:
            profile.public_key = f.read()
        with open(os.path.join(test_path, "id_rsa"), 'r') as f:
            profile.private_key = f.read()
        profile.save()

        self.cluster = Cluster(**CLUSTER)
        self.cluster.save()
        self.credential = Credential(user=self.user, cluster=self.cluster, **CREDENTIAL)
        self.credential.save()
        self.credential2 = Credential(user=super_user, cluster=self.cluster, **CREDENTIAL)
        self.credential2.save()

    def test_run_standard_jobs_staff_error(self):
        results = utils.run_standard_jobs(self.credential, [''], {}, {})
        self.assertEqual(results["error"], SUBMIT_ERROR)

    def test_run_standard_jobs_invalid_credential(self):
        results = utils.run_standard_jobs(None, [''], {}, {})
        self.assertEqual(results["error"], CRED_ERROR)

    def test_run_standard_jobs(self):
        job = 'sleep 10'
        names = "TON,CON"
        results = utils.run_standard_jobs(self.credential2, names, {}, {'jobstring': job})
        self.assertEqual(results["error"], None)
        self.assertEqual(results["failed"], [])

    def test_run_standard_jobs_name_error(self):
        job = 'sleep 10'
        names = "E-N,C-N"
        results = utils.run_standard_jobs(self.credential2, names, {}, {'jobstring': job})
        for name, error in results['failed']:
            self.assertEqual(error, "Bad Substituent Name(s): ['N']")


class UploadsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index(self):
        response = self.client.get(reverse(views.upload_data))
        self.assertEqual(response.status_code, 200)

    def test_log_parse(self):
        test_path = os.path.join(settings.MEDIA_ROOT, "tests")
        with open(os.path.join(test_path, "A_TON_A_A.log"), 'r') as f:
            data = {
                "files": f,
                "options": "logparse",
            }
            response = self.client.post(reverse(views.upload_data), data)
            self.assertEqual(response.status_code, 200)
            with StringIO(response.content) as f:
                reader = csv.reader(f, delimiter=',', quotechar='"')
                expected = ["A_TON_A_A.log", "A_TON_A_A",
                            "A_TON_A_A_n1_m1_x1_y1_z1",
                            "opt B3LYP/6-31g(d) geom=connectivity",
                            "-6.46079886952",
                            "-1.31975211714",
                            "41",
                            "0.0006",
                            "-567.1965205",
                            "---",
                            "0.35"]
                lines = [x for x in reader]
                results = lines[1][:3] + lines[1][4:]
                self.assertEqual(results, expected)

    def test_gjf_reset(self):
        base = os.path.join(settings.MEDIA_ROOT, "tests", "A_TON_A_A")
        with open(base + ".log", 'r') as log, open(base + ".gjf", 'r') as gjf:
            data = {
                "files": log,
                "options": "gjfreset",
            }
            response = self.client.post(reverse(views.upload_data), data)
            self.assertEqual(response.status_code, 200)
            with StringIO(response.content) as f:
                with zipfile.ZipFile(f, "r") as zfile:
                    with zfile.open("A_TON_A_A.gjf") as f2:
                        self.assertEqual(f2.read(), gjf.read())

    def test_gjf_reset_td(self):
        base = os.path.join(settings.MEDIA_ROOT, "tests", "A_TON_A_A")
        log_path = base + ".log"
        gjf_path = base + "_TD.gjf"
        with open(log_path, 'r') as log, open(gjf_path, 'r') as gjf:
            data = {
                "files": log,
                "options": "gjfreset",
                "td_reset": True,
            }
            response = self.client.post(reverse(views.upload_data), data)
            self.assertEqual(response.status_code, 200)
            with StringIO(response.content) as f:
                with zipfile.ZipFile(f, "r") as zfile:
                    with zfile.open("A_TON_A_A_TD.gjf") as f2:
                        self.assertEqual(f2.read(), gjf.read())

    def test_gjf_reset_fail(self):
        base = os.path.join(settings.MEDIA_ROOT, "tests", "A_TON_A_A")
        with open(base + ".gjf", 'r') as gjf:
            data = {
                "files": gjf,
                "options": "gjfreset",
            }
            response = self.client.post(reverse(views.upload_data), data)
            self.assertEqual(response.status_code, 200)
            with StringIO(response.content) as f:
                with zipfile.ZipFile(f, "r") as zfile:
                    with zfile.open("errors.txt") as f2:
                        msg = "A_TON_A_A.gjf - The log file was invalid"
                        self.assertEqual(f2.read(), msg)

    def test_data_parse(self):
        datatxt = os.path.join(settings.MEDIA_ROOT, "tests", "data.txt")
        outputtxt = os.path.join(settings.MEDIA_ROOT, "tests", "output.txt")
        with open(datatxt, 'r') as txt:
            data = {
                "files": txt,
                "options": "longchain",
            }
            response = self.client.post(reverse(views.upload_data), data)
            self.assertEqual(response.status_code, 200)
            with StringIO(response.content) as f, open(outputtxt, 'r') as out:
                with zipfile.ZipFile(f, "r") as zfile:
                    with zfile.open("output.txt") as f2:
                        self.assertEqual(f2.read(), out.read())

    def test_data_parse_set(self):
        for filename in ["CON.tar.gz", "TON.tar.bz2"]:
            filepath = os.path.join(settings.MEDIA_ROOT, "tests", filename)
            with open(filepath, 'r') as zfile:
                data = {
                    "files": zfile,
                    "options": "longchain",
                }
                response = self.client.post(reverse(views.upload_data), data)
                self.assertEqual(response.status_code, 200)
                with StringIO(response.content) as f:
                    with zipfile.ZipFile(f, "r") as zfile2:
                        with zfile2.open("output.txt") as f2:
                            self.assertIn("Errors (0)", f2.read())

    def test_data_parse_set_invalid(self):
        filepath = os.path.join(settings.MEDIA_ROOT, "tests", "A_TON_A_A.log")
        with open(filepath, 'r') as file:
            data = {
                "files": file,
                "options": "longchain",
            }
            response = self.client.post(reverse(views.upload_data), data)
            self.assertEqual(response.status_code, 200)
            msg = "There are no data files to parse."
            self.assertIn(msg, response.content)

    def test_data_parse_multi_set(self):
        filepath = os.path.join(settings.MEDIA_ROOT, "tests", "both.zip")
        with open(filepath, 'r') as zfile:
            data = {
                "files": zfile,
                "options": "longchain",
            }
            response = self.client.post(reverse(views.upload_data), data)
            self.assertEqual(response.status_code, 200)
            with StringIO(response.content) as f:
                with zipfile.ZipFile(f, "r") as zfile2:
                    for folder in ["CON__TD/", "TON__TD/"]:
                        with zfile2.open(folder + "output.txt") as f2:
                            self.assertIn("Errors (0)", f2.read())

    def test_view_gjf(self):
        name = os.path.join(settings.MEDIA_ROOT, "tests", "A_TON_A_A.gjf")
        with open(name, 'r') as log:
            data = {
                "files": log,
                "options": "gjfview",
            }
            response = self.client.post(reverse(views.upload_data), data)
            self.assertEqual(response.status_code, 200)

    # def test_data_parse_log(self):
    #     test_path = os.path.join(settings.MEDIA_ROOT, "tests")
    #     with open(os.path.join(test_path, "A_TON_A_A.log"), 'r') as f:
    #         data = {
    #             "files": f,
    #             "options": "dataparse",
    #         }
    #         response = self.client.post(reverse(views.upload_data), data)
    #     self.assertEqual(response.status_code, 200)

    def test_parse_without_data(self):
        data = {
            "files": '',
            "options": "dataparse",
        }
        response = self.client.post(reverse(views.upload_data), data)
        self.assertEqual(response.status_code, 200)
