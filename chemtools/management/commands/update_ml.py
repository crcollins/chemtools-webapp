from django.core.management.base import BaseCommand, CommandError

from chemtools.update_ml import run_all


class Command(BaseCommand):
    args = ''
    help = 'Update ML data'

    def handle(self, *args, **options):
        run_all()
