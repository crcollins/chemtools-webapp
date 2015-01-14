from django.core.management.base import BaseCommand

from cluster.update_jobs import run_all


class Command(BaseCommand):
    args = ''
    help = 'Update Job data from clusters'

    def handle(self, *args, **options):
        run_all()
