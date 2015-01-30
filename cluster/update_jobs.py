import logging

from django.contrib.auth.models import User

from utils import get_jobs


logger = logging.getLogger(__name__)


def run_all():
	logger.debug("Updating all the jobs")
    for user in User.objects.all():
        creds = user.credentials.all()
        get_jobs(creds)


if __name__ == "__main__":
    run_all()
