import os
from unittest import skipUnless
import time
import json

from django.conf import settings
from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.management import call_command

import views
import models
import utils
import interface
import update_jobs
import update_unknown
from account.views import account_page
from project.utils import get_sftp_connection, get_ssh_connection, AESCipher
from project.utils import SSHClient, SFTPClient, server_exists


SERVER = {
    "hostname": "localhost",
    "port": 2222,
    "username": "vagrant",
    "password": "vagrant",
}
USER_LOGIN = {
    "username": "testerman",
    "password": "S0m3thing",
}
USER = USER_LOGIN.copy()
USER["email"] = "test@test.com"

SUPER_USER_LOGIN = {
    "username": "admin",
    "password": "cantstopmenow",
}
SUPER_USER = SUPER_USER_LOGIN.copy()
SUPER_USER["email"] = "admin@test.com"

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
CREDENTIAL2 = {
    "username": "vagrant",
    "use_password": False,
    "password": '',
}
BAD_CREDENTIAL = {
    "username": "fails",
    "password": "fails",
    "use_password": False,
}
SUBMIT_ERROR = "You must be a staff user to submit a job."
KILL_ERROR = "You must be a staff user to kill a job."
CRED_ERROR = "Invalid credential"


def run_fake_job(credential):
    gjfstring = "EMPTY"
    jobstring = "sleep 0"
    results = interface.run_job(credential, gjfstring, jobstring)
    return results["jobid"]


class SSHPageTestCase(TestCase):

    def setUp(self):
        user = User.objects.create_user(**USER)
        user.save()
        self.user = user
        super_user = User.objects.create_superuser(**SUPER_USER)
        super_user.save()

        self.cluster = models.Cluster(**CLUSTER)
        self.cluster.save()
        self.credential = models.Credential(
            user=user, cluster=self.cluster, **CREDENTIAL)
        self.credential.save()

        self.credential2 = models.Credential(
            user=super_user, cluster=self.cluster, **CREDENTIAL)
        self.credential2.save()

        self.client = Client()

    def test_job_index(self):
        response = self.client.get(reverse(views.job_index))
        self.assertEqual(response.status_code, 302)

        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)
        response = self.client.get(reverse(views.job_index))
        self.assertEqual(response.status_code, 200)

    def test_cluster_job_index(self):
        url = reverse(views.cluster_job_index, args=(self.cluster.name, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @skipUnless(server_exists(**SERVER), "Requires external test server.")
    def test_job_detail(self):
        interface.run_job(self.credential2, '', 'sleep 10')
        results = interface.get_all_jobs(self.user, self.cluster.name)

        jobid = results[0]["jobs"][0][0]
        url = reverse(views.job_detail, args=(self.cluster.name, jobid))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @skipUnless(server_exists(**SERVER), "Requires external test server.")
    def test_job_detail_fail(self):
        url = reverse(views.job_detail, args=(self.cluster.name, 100000000000))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("That job number is not running.", response.content)

    def test_get_job_list(self):
        response = self.client.get(reverse(views.get_job_list))
        self.assertEqual(response.status_code, 302)

    def test_get_job_list_auth(self):
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)

        response = self.client.get(reverse(views.get_job_list))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["is_authenticated"])

    def test_get_job_list_html(self):
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)

        url = reverse(views.get_job_list) + "?html=true"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @skipUnless(server_exists(**SERVER), "Requires external test server.")
    def test_kill_job(self):
        url = reverse(views.kill_job, args=(CLUSTER['name'], ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        r = self.client.login(**SUPER_USER_LOGIN)
        self.assertTrue(r)

        jobid = run_fake_job(self.credential2)
        data = {
            jobid: "on",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

    @skipUnless(server_exists(**SERVER), "Requires external test server.")
    def test_kill_job_invalid(self):
        url = reverse(views.kill_job, args=(CLUSTER['name'], ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        r = self.client.login(**SUPER_USER_LOGIN)
        self.assertTrue(r)
        data = {
            "not an int": "on",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

    def test_kill_job_perm_fail(self):
        url = reverse(views.kill_job, args=(CLUSTER['name'], ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)
        data = {
            "123": "on",
            "234": "on",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content,
                         "You must be a staff user to kill a job.")

    def test_kill_job_redirect(self):
        url = reverse(views.kill_job, args=(CLUSTER['name'], ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)


class SSHSettingsTestCase(TestCase):

    def setUp(self):
        user = User.objects.create_user(**USER)
        user.save()
        profile = user.get_profile()
        test_path = os.path.join(settings.MEDIA_ROOT, "tests")
        with open(os.path.join(test_path, "id_rsa.pub"), 'r') as f:
            profile.public_key = f.read()
        with open(os.path.join(test_path, "id_rsa"), 'r') as f:
            profile.private_key = f.read()
        profile.save()

        self.cluster = models.Cluster(**CLUSTER)
        self.cluster.save()
        self.credential = models.Credential(
            user=user, cluster=self.cluster, **CREDENTIAL)
        self.credential.save()
        self.credential2 = models.Credential(
            user=user, cluster=self.cluster, **CREDENTIAL2)
        self.credential2.save()
        self.client = Client()

    def test_add_cluster(self):
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)

        url = reverse(account_page, args=(USER["username"], "clusters"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = {
            "name": "test-machine",
            "hostname": "test-machine.com",
            "port": 22,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Settings Successfully Saved", response.content)

    @skipUnless(server_exists(**SERVER), "Requires external test server.")
    def test_add_credential_password(self):
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)
        url = reverse(account_page, args=(USER["username"], "credentials"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "username": "vagrant",
            "password": "vagrant",
            "password2": "vagrant",
            "cluster": self.cluster.id,
            "use_password": True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Settings Successfully Saved", response.content)

    def test_add_credential_invalid_password(self):
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)

        url = reverse(account_page, args=(USER["username"], "credentials"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "username": "vagrant",
            "password": "incorrect",
            "password2": "password",
            "cluster": self.cluster.id,
            "use_password": True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Your passwords do not match", response.content)

    @skipUnless(server_exists(**SERVER), "Requires external test server.")
    def test_add_credential_key(self):
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)

        url = reverse(account_page, args=(USER["username"], "credentials"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "username": "vagrant",
            "cluster": self.cluster.id,
            "use_password": False,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Settings Successfully Saved", response.content)

    @skipUnless(server_exists(**SERVER), "Requires external test server.")
    def test_test_credential(self):
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)

        url = reverse(account_page, args=(USER["username"], "credentials"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "test": "on",
            "vagrant@localhost:2222-1": "on",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('class="success"', response.content)

    def test_test_credential_fail(self):
        user = User.objects.get(username=USER["username"])
        cred = models.Credential(user=user,
                                 cluster=self.cluster,
                                 **BAD_CREDENTIAL)
        cred.save()

        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)

        url = reverse(account_page, args=(USER["username"], "credentials"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "test": "on",
            cred.get_long_name(): "on",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('class="danger"', response.content)

    @skipUnless(server_exists(**SERVER), "Requires external test server.")
    def test_test_credential_both(self):
        user = User.objects.get(username=USER["username"])
        cred = models.Credential(user=user,
                                 cluster=self.cluster,
                                 **BAD_CREDENTIAL)
        cred.save()

        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)

        url = reverse(account_page, args=(USER["username"], "credentials"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "test": "on",
            cred.get_long_name(): "on",
            "vagrant@localhost:2222-1": "on",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('class="danger"', response.content)
        self.assertIn('class="success"', response.content)

    def test_delete_credential(self):
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)

        url = reverse(account_page, args=(USER["username"], "credentials"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "delete": "on",
            "vagrant@localhost:2222-1": "on",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Settings Successfully Saved", response.content)

    def test_delete_credential_invalid(self):
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)

        url = reverse(account_page, args=(USER["username"], "credentials"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "delete": "on",
            "sd@meh:22-1": "on",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Settings Successfully Saved", response.content)

    def test_delete_multi_credential(self):
        r = self.client.login(**USER_LOGIN)
        self.assertTrue(r)

        url = reverse(account_page, args=(USER["username"], "credentials"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "delete": "on",
            "vagrant@localhost:2222-1": "on",
            "vagrant@localhost:2222-2": "on",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Settings Successfully Saved", response.content)

    @skipUnless(server_exists(**SERVER), "Requires external test server.")
    def test_credential_ssh(self):
        with self.credential.get_ssh_connection():
            pass
        with self.credential2.get_ssh_connection():
            pass

    @skipUnless(server_exists(**SERVER), "Requires external test server.")
    def test_credential_sftp(self):
        with self.credential.get_sftp_connection():
            pass
        with self.credential2.get_sftp_connection():
            pass

    @skipUnless(server_exists(**SERVER), "Requires external test server.")
    def test_get_ssh_connection_obj(self):
        ssh = self.credential.get_ssh_connection()
        self.assertTrue(isinstance(ssh, SSHClient))
        obj = utils.get_ssh_connection_obj(self.credential)
        self.assertTrue(isinstance(obj, SSHClient))

    @skipUnless(server_exists(**SERVER), "Requires external test server.")
    def test_get_ssh_connection_obj_SSHClient(self):
        ssh = self.credential.get_ssh_connection()
        self.assertEqual(utils.get_ssh_connection_obj(ssh), ssh)

    def test_get_ssh_connection_obj_fail(self):
        obj = []
        with self.assertRaises(TypeError):
            utils.get_ssh_connection_obj(obj)

    @skipUnless(server_exists(**SERVER), "Requires external test server.")
    def test_get_sftp_connection_obj(self):
        sftp = self.credential.get_sftp_connection()
        self.assertTrue(isinstance(sftp, SFTPClient))
        obj = utils.get_sftp_connection_obj(self.credential)
        self.assertTrue(isinstance(obj, SFTPClient))

    @skipUnless(server_exists(**SERVER), "Requires external test server.")
    def test_get_sftp_connection_obj_SFTPClient(self):
        sftp = self.credential.get_sftp_connection()
        self.assertEqual(utils.get_sftp_connection_obj(sftp), sftp)

    def test_get_sftp_connection_obj_fail(self):
        obj = []
        with self.assertRaises(TypeError):
            utils.get_sftp_connection_obj(obj)


class UtilsTestCase(TestCase):

    @skipUnless(server_exists(**SERVER), "Requires external test server.")
    def test_get_sftp_password(self):
        sftp = get_sftp_connection("localhost", "vagrant",
                                   password="vagrant", port=2222)
        with sftp:
            pass

    @skipUnless(server_exists(**SERVER), "Requires external test server.")
    def test_get_sftp_key(self):
        test_path = os.path.join(settings.MEDIA_ROOT, "tests")
        with open(os.path.join(test_path, "id_rsa"), 'r') as key:
            sftp = get_sftp_connection("localhost", "vagrant",
                                       key=key, port=2222)
            with sftp:
                pass

    def test_get_sftp_error(self):
        with self.assertRaises(Exception):
            with get_sftp_connection("localhost", "username"):
                pass

    @skipUnless(server_exists(**SERVER), "Requires external test server.")
    def test_get_ssh_password(self):
        ssh = get_ssh_connection("localhost", "vagrant",
                                 password="vagrant", port=2222)
        with ssh:
            pass

    @skipUnless(server_exists(**SERVER), "Requires external test server.")
    def test_get_ssh_key(self):
        test_path = os.path.join(settings.MEDIA_ROOT, "tests")
        with open(os.path.join(test_path, "id_rsa"), 'r') as key:
            ssh = get_ssh_connection("localhost", "vagrant",
                                     key=key, port=2222)
            with ssh:
                pass

    def test_get_ssh_error(self):
        with self.assertRaises(Exception):
            get_ssh_connection("localhost", "username")

    def test__get_jobs_fail(self):
        results = [None]
        utils._get_jobs(None, None, 0, results)
        expected = [
            {
                'jobs': [],
                'name': None,
                'columns': ['Job ID', 'Username', 'Jobname',
                            "Req'd Memory", "Req'd Time", 'Elap Time', 'S']
            }
        ]
        self.assertEqual(results, expected)

    def test_AES(self):
        cipher = AESCipher()
        string = "The quick brown fox jumps over the lazy dog."
        ct = cipher.encrypt(string)
        pt = cipher.decrypt(ct)
        self.assertEqual(pt, string)

    def test_AES_error(self):
        cipher = AESCipher()
        string = "The quick brown fox jumps over the lazy dog."
        ct = cipher.encrypt(string)[:10] + "randomgarbage"
        self.assertRaises(TypeError, cipher.decrypt, ct)


@skipUnless(server_exists(**SERVER), "Requires external test server.")
class InterfaceTestCase(TestCase):

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

        self.cluster = models.Cluster(**CLUSTER)
        self.cluster.save()
        self.credential = models.Credential(
            user=self.user, cluster=self.cluster, **CREDENTIAL)
        self.credential.save()
        self.credential2 = models.Credential(
            user=super_user, cluster=self.cluster, **CREDENTIAL)
        self.credential2.save()
        self.client = Client()

    def test_run_job_folder_error(self):
        with self.credential2.get_ssh_connection() as ssh:
            ssh.exec_command(
                "sudo chown root:root chemtools; sudo chmod 700 chemtools")
            results = interface.run_job(
                self.credential2, '', jobstring='sleep 0')
            ssh.exec_command(
                "sudo chown vagrant:vagrant chemtools; chmod 775 chemtools")
            self.assertIn('mkdir: cannot create directory', results["error"])

    def test_run_job_staff_error(self):
        results = interface.run_job(self.credential, '', jobstring=None)
        self.assertEqual(results["error"], SUBMIT_ERROR)

    def test_run_job_invalid_credential(self):
        results = interface.run_job(None, '', jobstring=None)
        self.assertEqual(results["error"], CRED_ERROR)

    def test_run_job(self):
        results = interface.run_job(self.credential2, '', jobstring='sleep 0')
        self.assertEqual(results["error"], None)

    def test_run_jobs_staff_error(self):
        results = interface.run_jobs(self.credential, [], [], jobstring=None)
        self.assertEqual(results["error"], SUBMIT_ERROR)

    def test_run_jobs_invalid_credential(self):
        results = interface.run_jobs(None, [], [], jobstring=None)
        self.assertEqual(results["error"], CRED_ERROR)

    def test_run_jobs(self):
        names = ['test', 'test2']
        gjfs = ['', '']
        job = 'sleep 0'
        results = interface.run_jobs(
            self.credential2, names, gjfs, jobstring=job)
        self.assertEqual(results["error"], None)

    def test_run_jobs_qsub_error(self):
        names = ['benz; ls files.gjf']
        gjfs = ['']
        job = 'sleep 0'
        results = interface.run_jobs(
            self.credential2, names, gjfs, jobstring=job)
        self.assertIn("qsub -", results["failed"][0][1])

    def test_run_job_states(self):
        results = interface.run_job(self.credential2, '', jobstring='sleep 10')
        jobid = results["jobid"]
        self.assertEqual(results["error"], None)
        job = models.Job.objects.get(jobid=jobid)
        self.assertEqual(job.state, models.Job.QUEUED)
        update_jobs.run_all()
        job = models.Job.objects.get(jobid=jobid)
        self.assertEqual(job.state, models.Job.RUNNING)
        time.sleep(10)
        update_jobs.run_all()
        job = models.Job.objects.get(jobid=jobid)
        self.assertEqual(job.state, models.Job.COMPLETED)

    def test_kill_jobs_staff_error(self):
        results = interface.kill_jobs(self.credential, [''])
        self.assertEqual(results["error"], KILL_ERROR)

    def test_kill_jobs_invalid_credential(self):
        results = interface.kill_jobs(None, [''])
        self.assertEqual(results["error"], CRED_ERROR)

    def test_kill_jobs_run_through(self):
        results = interface.run_job(self.credential2, '', jobstring='sleep 10')
        jobid = results["jobid"]
        results = interface.kill_jobs(self.credential2, [jobid])
        self.assertEqual(results["error"], None)

    def test_kill_jobs_run_through_no_job(self):
        results = interface.run_job(self.credential2, '', jobstring='sleep 10')
        jobid = results["jobid"]
        models.Job.objects.filter(
            credential=self.credential2, jobid=jobid).delete()
        results = interface.kill_jobs(self.credential2, [jobid])
        self.assertEqual(results["error"], None)

    def test_get_specific_jobs_invalid_credential(self):
        results = interface.get_specific_jobs(None, [])
        self.assertEqual(results["error"], CRED_ERROR)

    def test_get_specific_jobs_no_match(self):
        results = interface.get_specific_jobs(self.credential, [])
        expected = {
            'cluster': CLUSTER["name"],
            'failed': [],
            'worked': [],
            'error': None
        }
        self.assertEqual(results, expected)

    def test_get_all_jobs(self):
        results = interface.get_all_jobs(self.user)
        results[0]["jobs"] = []
        expected = [
            {
                'jobs': [],
                'name': CLUSTER['name'],
                'columns': [
                    'Job ID',
                    'Username',
                    'Jobname',
                    "Req'd Memory",
                    "Req'd Time",
                    'Elap Time',
                    'S'
                ]
            }
        ]
        self.assertEqual(results, expected)

    def test_get_all_log_data(self):
        results = interface.get_all_log_data(self.credential2)
        self.assertEqual(results["error"], None)
        self.assertIn("Filename", results["results"])

    def test_get_all_log_data_argparse(self):
        with self.credential2.get_sftp_connection() as sftp:
            with sftp.open("chemtools/fileparser.py", 'w') as f:
                f.write("from __future__ import print_function\n")
                f.write("import sys\n")
                f.write("print('No module named argparse', file=sys.stderr)")

        results = interface.get_all_log_data(self.credential2)
        self.assertIn("No module named argparse", results["error"])

        with self.credential2.get_ssh_connection() as ssh:
            ssh.exec_command("rm chemtools/fileparser.py")

    def test_get_all_log_data_invalid_credential(self):
        results = interface.get_all_log_data(None)
        self.assertEqual(results["error"], CRED_ERROR)

    def test_get_log_data_error(self):
        results = interface.get_log_data(self.credential2, [""])
        self.assertIn("IndexError", results["error"])

    def test_get_log_data_argparse(self):
        with self.credential2.get_sftp_connection() as sftp:
            with sftp.open("chemtools/fileparser.py", 'w') as f:
                f.write("from __future__ import print_function\n")
                f.write("import sys\n")
                f.write("print('No module named argparse', file=sys.stderr)")

        results = interface.get_log_data(self.credential2, [""])
        self.assertIn("No module named argparse", results["error"])

        with self.credential2.get_ssh_connection() as ssh:
            ssh.exec_command("rm chemtools/fileparser.py")

    def test_get_log_data_invalid_credential(self):
        results = interface.get_log_data(None, "24a_TON")
        self.assertEqual(results["error"], CRED_ERROR)

    def test_get_log_status_invalid_credential(self):
        results = interface.get_log_status(None, ["24a_TON"])
        self.assertEqual(results["error"], CRED_ERROR)


@skipUnless(server_exists(**SERVER), "Requires external test server.")
class ManagementTestCase(TestCase):

    def setUp(self):
        super_user = User.objects.create_superuser(**SUPER_USER)
        super_user.save()

        self.cluster = models.Cluster(**CLUSTER)
        self.cluster.save()
        self.credential = models.Credential(
            user=super_user, cluster=self.cluster, **CREDENTIAL)
        self.credential.save()
        with self.credential.get_ssh_connection() as ssh:
            ssh.exec_command("touch chemtools/walltime.log")
            ssh.exec_command("touch chemtools/done/failed.log")
            c = "echo 'Normal termination of Gaussian' > chemtools/done/completed.log"
            ssh.exec_command(c)

    def test_update_jobs(self):
        job = models.Job(credential=self.credential,
                         jobid="1",
                         name="not_a_real_job")
        job.save()
        update_jobs.run_all()
        updated = models.Job.objects.get(id=job.id)
        self.assertEqual(updated.state, models.Job.UNKNOWN)

    def test_update_jobs_command(self):
        job = models.Job(credential=self.credential,
                         jobid="1",
                         name="not_a_real_job")
        job.save()
        call_command("update_jobs")
        updated = models.Job.objects.get(id=job.id)
        self.assertEqual(updated.state, models.Job.UNKNOWN)

    def test_update_unknown_walltime(self):
        job = models.Job(credential=self.credential,
                         jobid="1",
                         name="walltime",
                         state=models.Job.UNKNOWN)
        job.save()
        update_unknown.run_all()
        updated = models.Job.objects.get(id=job.id)
        self.assertEqual(updated.state, models.Job.WALLTIME)

    def test_update_unknown_completed(self):
        job = models.Job(credential=self.credential,
                         jobid="1",
                         name="completed",
                         state=models.Job.UNKNOWN)
        job.save()
        update_unknown.run_all()
        updated = models.Job.objects.get(id=job.id)
        self.assertEqual(updated.state, models.Job.COMPLETED)

    def test_update_unknown_failed(self):
        job = models.Job(credential=self.credential,
                         jobid="1",
                         name="failed",
                         state=models.Job.UNKNOWN)
        job.save()
        update_unknown.run_all()
        updated = models.Job.objects.get(id=job.id)
        self.assertEqual(updated.state, models.Job.FAILED)

    def test_update_unknown_missing(self):
        job = models.Job(credential=self.credential,
                         jobid="1",
                         name="missing",
                         state=models.Job.UNKNOWN)
        job.save()
        update_unknown.run_all()
        updated = models.Job.objects.get(id=job.id)
        self.assertEqual(updated.state, models.Job.MISSING)

    def test_update_unknown_none(self):
        job = models.Job(credential=self.credential,
                         jobid="1",
                         name="completed",
                         state=models.Job.COMPLETED)
        job.save()
        update_unknown.run_all()
        update_unknown.run_all()

    def test_update_unknown_command(self):
        job = models.Job(credential=self.credential,
                         jobid="1",
                         name="walltime",
                         state=models.Job.UNKNOWN)
        job.save()
        call_command("update_unknown")
        updated = models.Job.objects.get(id=job.id)
        self.assertEqual(updated.state, models.Job.WALLTIME)


class ModelTestCase(TestCase):

    def setUp(self):
        super_user = User.objects.create_superuser(**SUPER_USER)
        super_user.save()

        self.cluster = models.Cluster(**CLUSTER)
        self.cluster.save()
        self.credential = models.Credential(
            user=super_user, cluster=self.cluster, **CREDENTIAL)
        self.credential.save()

    def test_job_format(self):
        job = models.Job(
            jobid='1',
            credential=self.credential,
            name="test",
            memory="59GB",
            walltime="1:00",
            state=models.Job.QUEUED,
        )
        expected = ('1', 'vagrant', 'test', '59GB', '1:00', '--', 'Q')
        self.assertEqual(job.format(), expected)
