import logging

from django.contrib.auth import get_user_model

from utils import get_jobs


logger = logging.getLogger(__name__)


def run_all():
    logger.debug("Updating all the jobs")
    for user in get_user_model().objects.all():
        creds = get_user_model().credentials.all()
        get_jobs(creds)


if __name__ == "__main__":
    run_all()
