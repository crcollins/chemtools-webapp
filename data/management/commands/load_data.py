from django.core.management.base import BaseCommand, CommandError
from data.load_data import main


class Command(BaseCommand):
    args = 'path'
    help = 'Load parsed data into the database'

    def handle(self, *args, **options):
        if not len(args):
            raise CommandError("Needs a path to a csv data file.")

        path = args[0]
        try:
            with open(path, 'r') as f:
                count = main(f)
        except IOError:
            raise CommandError("No such csv data file: '%s'" % path)

        self.stdout.write("Added %d datapoint(s)." % count)
