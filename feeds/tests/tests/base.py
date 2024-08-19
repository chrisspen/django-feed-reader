import os

import mock

from django.test import TestCase
from django.conf import settings


class BaseTests(TestCase):

    TEST_FILES_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../testdata")
    BASE_URL = 'http://feed.com/'

    def _populate_mock(self, mock, test_file, status, content_type, etag=None, headers=None, url=BASE_URL, is_cloudflare=False):

        with open(os.path.join(self.TEST_FILES_FOLDER, test_file), "rb") as fin:
            content = fin.read()

        ret_headers = {"Content-Type": content_type, "etag": "an-etag"}
        if headers is not None:
            ret_headers = {**ret_headers, **headers}

        {"Content-Type": content_type, "etag": "an-etag"}

        if is_cloudflare:
            agent = "{user_agent} (+{server}; Updater; {subs} subscribers)".format(user_agent=settings.FEEDS_USER_AGENT, server=settings.FEEDS_SERVER, subs=1)

            mock.register_uri('GET', url, request_headers={"User-Agent": agent}, status_code=status, content=content, headers=ret_headers)
        else:
            if etag is None:
                mock.register_uri('GET', url, status_code=status, content=content, headers=ret_headers)
            else:
                mock.register_uri('GET', url, request_headers={'If-None-Match': etag}, status_code=status, content=content, headers=ret_headers)
