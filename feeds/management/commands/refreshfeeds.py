from django.core.management.base import BaseCommand

from feeds.utils import update_feeds
from feeds.models import Source


class Command(BaseCommand):
    help = 'Rrefreshes the RSS feeds'

    def add_arguments(self, parser):
        parser.add_argument('--sources', default='')
        parser.add_argument('--force', default=False, action='store_true', help='If given, overrides any last-checked timestamps and forces a refresh.')

    def handle(self, *args, **options):

        source_ids = [int(_) for _ in options['sources'].split(',') if _.isdigit()]
        sources = None
        if source_ids:
            sources = Source.objects.filter(id__in=source_ids)

        update_feeds(30, self.stdout, sources=sources, force=options['force'])

        self.stdout.write(self.style.SUCCESS('Finished'))
