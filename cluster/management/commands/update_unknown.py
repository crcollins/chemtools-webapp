import logging

from django.core.management.base import BaseCommand

from cluster.models import Credential, Job
from cluster.interface import get_log_status


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ''
    help = 'Update unknown Job data from clusters'

    def handle(self, *args, **options):
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
