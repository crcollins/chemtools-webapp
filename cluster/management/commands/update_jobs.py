import logging

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from cluster.utils import get_jobs


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ''
    help = 'Update Job data from clusters'

    def handle(self, *args, **options):
	    logger.debug("Updating all the jobs")
	    for user in get_user_model().objects.all():
	        creds = get_user_model().credentials.all()
	        get_jobs(creds)
