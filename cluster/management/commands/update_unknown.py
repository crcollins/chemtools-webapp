from django.core.management.base import BaseCommand, CommandError

from cluster.update_unknown import run_all


class Command(BaseCommand):
    args = ''
    help = 'Update unknown Job data from clusters'

    def handle(self, *args, **options):
        run_all()
