from django.contrib.auth.models import User

from models import Job
from utils import get_jobs


def run_all():
    for user in User.objects.all():
        creds = user.credentials.all()
        get_jobs(creds)


if __name__ == "__main__":
    run_all()
