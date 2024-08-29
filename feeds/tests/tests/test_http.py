from datetime import timedelta
import requests_mock

from django.utils import timezone

from feeds.models import Source, WebProxy
from feeds.utils import read_feed, find_proxies, get_proxy

from .base import BaseTests


@requests_mock.Mocker()
class Tests(BaseTests):

    def test_fucking_cloudflare(self, mock):

        self._populate_mock(
            mock,
            status=200,
            test_file="proxy_list.txt",
            content_type="text/plain",
            url="https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt"
        )
        self._populate_mock(mock, status=200, test_file="json_simple_two_entry.json", content_type="application/json")
        self._populate_mock(mock, status=403, test_file="json_simple_two_entry.json", content_type="application/json", is_cloudflare=True)

        src = Source(name="test1", feed_url=self.BASE_URL, interval=0, is_cloudflare=False)
        src.save()

        # Read the feed once to get the 1 post  and the etag
        read_feed(src)
        self.assertEqual(src.status_code, 403)

        src = Source(name="test2", feed_url=self.BASE_URL, interval=0, is_cloudflare=True)
        src.save()

        # Read the feed once to get the 1 post  and the etag
        read_feed(src)
        self.assertEqual(src.status_code, 200)

    def test_find_proxies(self, mock):

        self._populate_mock(mock, status=200, test_file="proxy_list.html", content_type="text/html", url="http://www.workingproxies.org")

        find_proxies()

        self.assertEqual(WebProxy.objects.count(), 20)

    def test_get_proxy(self, mock):

        self._populate_mock(mock, status=200, test_file="proxy_list.html", content_type="text/html", url="http://www.workingproxies.org")

        p = get_proxy()

        self.assertIsNotNone(p)

    def test_etags(self, mock):

        self._populate_mock(mock, status=200, test_file="rss_xhtml_body.xml", content_type="application/xml+rss")
        self._populate_mock(mock, status=304, test_file="empty_file.txt", content_type="application/xml+rss", etag="an-etag")

        src = Source(name="test1", feed_url=self.BASE_URL, interval=0)
        src.save()

        # Read the feed once to get the 1 post  and the etag
        read_feed(src)
        self.assertEqual(src.status_code, 200)
        self.assertEqual(src.posts.count(), 1) # got the one post
        self.assertEqual(src.interval, 60)
        self.assertEqual(src.etag, "an-etag")

        # Read the feed again to get a 304 and a small increment to the interval
        read_feed(src)
        self.assertEqual(src.posts.count(), 1) # should have no more
        self.assertEqual(src.status_code, 304)
        self.assertEqual(src.interval, 70)
        self.assertTrue(src.live)

    def test_not_a_feed(self, mock):

        self._populate_mock(mock, status=200, test_file="spurious_text_file.txt", content_type="text/plain")

        src = Source(name="test1", feed_url=self.BASE_URL, interval=0)
        src.save()

        read_feed(src)
        self.assertEqual(src.status_code, 200) # it returned a page, but not a  feed
        self.assertEqual(src.posts.count(), 0) # can't have got any
        self.assertEqual(src.interval, 120)
        self.assertTrue(src.live)

    def test_permission_denied(self, mock):

        self._populate_mock(mock, status=403, test_file="empty_file.txt", content_type="text/plain")

        src = Source(name="test1", feed_url=self.BASE_URL, interval=0, live=True)
        src.save()

        read_feed(src)
        self.assertEqual(src.status_code, 403) # it returned a page, but not a  feed
        self.assertEqual(src.posts.count(), 0) # can't have got any

        # Just because we momentarily received a 403 forbidden message,
        # don't automatically disable the source, because that's stupid.
        # We might have been accessing the server too quickly or the server might have a bug.
        self.assertTrue(src.live)

    def test_feed_gone(self, mock):

        self._populate_mock(mock, status=410, test_file="empty_file.txt", content_type="text/plain")

        src = Source(name="test1", feed_url=self.BASE_URL, interval=0)
        src.save()

        read_feed(src)
        self.assertEqual(src.status_code, 410) # it returned a page, but not a  feed
        self.assertEqual(src.posts.count(), 0) # can't have got any
        # Again, don't automatically disable sources!
        self.assertTrue(src.live)

    def test_feed_not_found(self, mock):

        self._populate_mock(mock, status=404, test_file="empty_file.txt", content_type="text/plain")

        src = Source(name="test1", feed_url=self.BASE_URL, interval=0)
        src.save()

        read_feed(src)
        self.assertEqual(src.status_code, 404) # it returned a page, but not a  feed
        self.assertEqual(src.posts.count(), 0) # can't have got any
        self.assertTrue(src.live)
        self.assertEqual(src.interval, 120)

    def test_temp_redirect(self, mock):

        new_url = "http://new.feed.com/"
        self._populate_mock(mock, status=302, test_file="empty_file.txt", content_type="text/plain", headers={"Location": new_url})
        self._populate_mock(mock, status=200, test_file="rss_xhtml_body.xml", content_type="application/xml+rss", url=new_url)

        src = Source(name="test1", feed_url=self.BASE_URL, interval=0)
        src.save()

        self.assertIsNone(src.last_302_start)

        read_feed(src)
        self.assertEqual(src.status_code, 200)
        self.assertEqual(src.last_302_url, new_url) # this is where  went
        self.assertIsNotNone(src.last_302_start)
        self.assertEqual(src.posts.count(), 1) # after following redirect will have 1 post
        self.assertEqual(src.interval, 60)
        self.assertTrue(src.live)

        # do it all again -  shouldn't change
        read_feed(src)
        self.assertEqual(src.status_code, 200) # it returned a page, but not a  feed
        self.assertEqual(src.last_302_url, new_url) # this is where  went
        self.assertIsNotNone(src.last_302_start)
        self.assertEqual(src.posts.count(), 1) # after following redirect will have 1 post
        self.assertEqual(src.interval, 80)
        self.assertTrue(src.live)

        # now we test making it permaent
        src.last_302_start = timezone.now() - timedelta(days=365)
        src.save()
        read_feed(src)
        self.assertEqual(src.status_code, 200)
        self.assertEqual(src.last_302_url, ' ')
        self.assertIsNone(src.last_302_start)
        self.assertEqual(src.posts.count(), 1)
        self.assertEqual(src.interval, 100)
        self.assertEqual(src.feed_url, new_url)
        self.assertTrue(src.live)

    def test_perm_redirect(self, mock):

        new_url = "http://new.feed.com/"
        self._populate_mock(mock, status=301, test_file="empty_file.txt", content_type="text/plain", headers={"Location": new_url})
        self._populate_mock(mock, status=200, test_file="rss_xhtml_body.xml", content_type="application/xml+rss", url=new_url)

        src = Source(name="test1", feed_url=self.BASE_URL, interval=0)
        src.save()

        read_feed(src)
        self.assertEqual(src.status_code, 301)
        self.assertEqual(src.interval, 60)
        self.assertEqual(src.feed_url, new_url)

        read_feed(src)
        self.assertEqual(src.status_code, 200)
        self.assertEqual(src.posts.count(), 1)
        self.assertEqual(src.interval, 60)
        self.assertTrue(src.live)

    def test_server_error_1(self, mock):

        self._populate_mock(mock, status=500, test_file="empty_file.txt", content_type="text/plain")

        src = Source(name="test1", feed_url=self.BASE_URL, interval=0)
        src.save()

        read_feed(src)
        self.assertEqual(src.status_code, 500) # error
        self.assertEqual(src.posts.count(), 0) # can't have got any
        self.assertTrue(src.live)
        self.assertEqual(src.interval, 120)

    def test_server_error_2(self, mock):

        self._populate_mock(mock, status=503, test_file="empty_file.txt", content_type="text/plain")

        src = Source(name="test1", feed_url=self.BASE_URL, interval=0)
        src.save()

        read_feed(src)
        self.assertEqual(src.status_code, 503) # error!
        self.assertEqual(src.posts.count(), 0) # can't have got any
        self.assertTrue(src.live)
        self.assertEqual(src.interval, 120)
