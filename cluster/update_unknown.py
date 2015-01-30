import logging

from models import Credential, Job
from interface import get_log_status


logger = logging.getLogger(__name__)


def run_all():
    logger.debug("Updating all unknown job states")
    for cred in Job.objects.values('credential').distinct():
        cred = Credential.objects.get(id=cred["credential"])
        jobs = Job.objects.filter(credential=cred, state=Job.UNKNOWN)

        if not jobs:
            continue

        jobids, names = zip(*jobs.values_list('jobid', 'name'))
        status = get_log_status(cred, names)

        d = {key: [] for key in status["results"]}
        for key, jobid in zip(status["results"], jobids):
            d[key].append(jobid)

        Job.update_states(cred, d)

if __name__ == "__main__":
    run_all()
