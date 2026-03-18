import requests_mock
from django.utils import timezone

from feeds.models import Source
from feeds.utils import read_feed

from .base import BaseTests


@requests_mock.Mocker()
class Tests(BaseTests):

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

    def test_double_escaped_html(self, mock):
        """
        Test that JSON feeds with double-escaped HTML (&lt;p&gt;) are properly
        unescaped to valid HTML (<p>).

        This was a bug where parse_feed_json only called feedparser's _sanitize_html
        but not our custom sanitize_html which includes unescape_double_escaped_html.
        """
        self._populate_mock(mock, status=200, test_file="json_double_escaped_html.json", content_type="application/json")

        src = Source(name="test1", feed_url=self.BASE_URL, interval=0)
        src.save()

        read_feed(src)
        self.assertEqual(src.status_code, 200)
        self.assertEqual(src.posts.count(), 1)

        post = src.posts.all().first()
        # The body should contain proper HTML tags, not escaped entities
        self.assertIn('<p>', post.body)
        self.assertIn('<strong>', post.body)
        # Should NOT contain double-escaped entities
        self.assertNotIn('&lt;p&gt;', post.body)
        self.assertNotIn('&lt;strong&gt;', post.body)

    def test_invalid_published_date_defaults_to_now(self, mock):
        content = """
        {
          "title": "Bad Date Feed",
          "items": [
            {
              "id": "bad-date-1",
              "title": "Ancient episode",
              "content_text": "hello",
              "date_published": "1968-12-01T00:00:00Z",
              "attachments": [
                {"url": "https://example.com/test.mp3", "mime_type": "audio/mpeg"}
              ]
            }
          ]
        }
        """
        mock.register_uri('GET', self.BASE_URL, status_code=200, text=content, headers={"Content-Type": "application/json", "etag": "an-etag"})

        src = Source(name="test1", feed_url=self.BASE_URL, interval=0)
        src.save()

        before = timezone.now()
        read_feed(src)
        after = timezone.now()

        post = src.posts.get()
        self.assertGreaterEqual(post.created, before)
        self.assertLessEqual(post.created, after)
