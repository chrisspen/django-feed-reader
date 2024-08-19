import requests_mock

from feeds.models import Source
from feeds.utils import read_feed

from .base import BaseTests


@requests_mock.Mocker()
class JSONFeedTests(BaseTests):

    def test_simple_json(self, mock):

        self._populate_mock(mock, status=200, test_file="json_simple_two_entry.json", content_type="application/json")

        src = Source(name="test1", feed_url=self.BASE_URL, interval=0)
        src.save()

        # Read the feed once to get the 1 post  and the etag
        read_feed(src)
        self.assertEqual(src.status_code, 200)
        self.assertEqual(src.posts.count(), 2) # got the one post
        self.assertEqual(src.interval, 60)
        self.assertEqual(src.etag, "an-etag")

    def test_sanitize_1(self, mock):

        self._populate_mock(mock, status=200, test_file="json_simple_two_entry.json", content_type="application/json")

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

        # Contains a feed with a malformed title attempting to inject Javascript.
        # If our sanitization works, the malformed parts will be removed, leaving behind the text "safe".
        self._populate_mock(mock, status=200, test_file="sanitizer_bad_comment.json", content_type="application/json")

        # Only sources with blank names will be auto-filled with a name.
        src = Source(name="", feed_url=self.BASE_URL, interval=0)
        src.save()

        # read the feed to update the name
        read_feed(src)
        self.assertEqual(src.status_code, 200)
        self.assertEqual(src.name, "safe")

    def test_podcast(self, mock):

        self._populate_mock(mock, status=200, test_file="podcast.json", content_type="application/json")

        src = Source(name="test1", feed_url=self.BASE_URL, interval=0)
        src.save()

        read_feed(src)
        self.assertEqual(src.status_code, 200)

        self.assertEqual(src.posts.count(), 1)
        post = src.posts.all().first()
        self.assertEqual(post.title, "Weekly Wrap: UFOs, Iran, Libra")

        self.assertEqual(post.enclosures.count(), 1)
        enc = post.enclosures.all().first()
        self.assertEqual(
            enc.href, "https://play.podtrac.com/npr-510317/edge1.pod.npr.org/anon.npr-mp3/npr/sam/2019/06/"
            "20190621_sam_wrap621.mp3?orgId=1&d=2353&p=510317&story=734830514&"
            "t=podcast&e=734830514&size=37575870&ft=pod&f=510317&awCollectionId=510317&"
            "awEpisodeId=734830514"
        )
