from django.core.management.base import BaseCommand, CommandError
from data.load_data import main


class Command(BaseCommand):
    args = 'path'
    help = 'Load parsed data into the database'

    def handle(self, path, *args, **options):
        main(path)
