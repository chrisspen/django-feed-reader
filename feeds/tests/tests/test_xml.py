import logging
import requests_mock

from feeds.models import Source
from feeds.utils import read_feed

from .base import BaseTests

logger = logging.getLogger(__name__)


@requests_mock.Mocker()
class Tests(BaseTests):

    def test_simple_xml(self, mock):

        self._populate_mock(mock, status=200, test_file="rss_xhtml_body.xml", content_type="application/rss+xml")

        src = Source(name="test1", feed_url=self.BASE_URL, interval=0)
        src.save()

        # Read the feed once to get the 1 post  and the etag
        read_feed(src)
        self.assertEqual(src.status_code, 200)
        self.assertEqual(src.posts.count(), 1) # got the one post
        self.assertEqual(src.interval, 60)
        self.assertEqual(src.etag, "an-etag")

    def test_podcast(self, mock):

        self._populate_mock(mock, status=200, test_file="podcast.xml", content_type="application/rss+xml")

        src = Source(name="test1", feed_url=self.BASE_URL, interval=0)
        src.save()

        # Read the feed once to get the 1 post  and the etag
        read_feed(src)

        self.assertEqual(src.description, 'SU: Three nerds discussing tech, Apple, programming, and loosely related matters.')

        self.assertEqual(src.posts.all()[0].enclosures.count(), 1)

    def test_sanitize_1(self, mock):
        """
            Make sure feedparser's sanitization is running
        """

        self._populate_mock(mock, status=200, test_file="rss_xhtml_body.xml", content_type="application/rss+xml")

        src = Source(name="test1", feed_url=self.BASE_URL, interval=0)
        src.save()

        # Read the feed once to get the 1 post  and the etag
        read_feed(src)
        self.assertEqual(src.status_code, 200)
        p = src.posts.all()[0]

        self.assertFalse("<script>" in p.body)

    def test_sanitize_2(self, mock):
        """
            Another test that the sanitization is going on.  This time we have
            stolen a test case from the feedparser libarary
        """

        self._populate_mock(mock, status=200, test_file="sanitizer_bad_comment.xml", content_type="application/rss+xml")

        src = Source(name="", feed_url=self.BASE_URL, interval=0)
        src.save()

        # read the feed to update the name
        read_feed(src)
        self.assertEqual(src.status_code, 200)
        self.assertEqual(src.name, "safe")

    def test_sanitize_attrs(self, mock):

        self._populate_mock(mock, status=200, test_file="sanitizer_img_attrs.xml", content_type="application/rss+xml")

        src = Source(name="test1", feed_url=self.BASE_URL, interval=0)
        src.save()

        # read the feed to update the name
        read_feed(src)
        self.assertEqual(src.status_code, 200)

        body = src.posts.all()[0].body

        self.assertTrue("<img" in body)
        self.assertFalse("align=" in body)
        self.assertFalse("hspace=" in body)

    def test_load_body(self, mock):

        self._populate_mock(mock, status=200, test_file="podcast_sample1.rss", content_type="application/rss+xml")

        src = Source(name="test1", feed_url=self.BASE_URL, interval=0)
        src.save()

        read_feed(src)
        self.assertEqual(src.status_code, 200)

        self.assertEqual(src.posts.count(), 1)

        post = src.posts.first()
        body = post.body

        logger.debug('Body: %s', body)
        self.assertTrue("<p><strong>Find my &quot;extra&quot; content on Locals: </strong>" in body)
