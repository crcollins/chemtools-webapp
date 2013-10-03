from django.core.management.base import BaseCommand, CommandError
from chemtools.extractor import run_all

class Command(BaseCommand):
    args = ''
    help = 'Extract mol2 data'

    def handle(self, *args, **options):
        run_all()