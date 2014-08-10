from django.contrib.auth.models import User

from models import Job
from interface import get_all_jobs, get_log_status


def run_all():
    for cred in Job.objects.values('credential').distinct():
        jobs = Job.objects.filter(credential=cred, status=Job.UNKNOWN)
        jobids, names = zip(*jobs.values_list('jobid', 'name'))
        status = get_log_status(cred, names)

        d = {key: [] for key in status["results"]}
        for key, jobid in zip(status["results"], jobids):
            d[key].append(jobid)

        Job.update_states(cred, d)

if __name__ == "__main__":
    run_all()
