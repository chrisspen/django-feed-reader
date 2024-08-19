import os

from django.core.management.base import BaseCommand

from feeds.utils import import_feed
from feeds.models import Source


class Command(BaseCommand):
    help = 'Imports an RSS feed file'

    def add_arguments(self, parser):
        parser.add_argument('source', default='')
        parser.add_argument('feed', default='')

    def handle(self, source, feed, *args, **options):
        source = Source.objects.get(id=int(source))
        feed_path = feed
        assert os.path.isfile(feed_path)
        with open(feed_path, 'r', encoding='utf-8') as fin:
            feed_body = fin.read()
            import_feed(source, feed_body=feed_body, content_type="xml", output=self.stdout)
        self.stdout.write(self.style.SUCCESS('Finished'))
