import logging
import requests_mock

from feeds.utils import sanitize_html, unescape_double_escaped_html

from .base import BaseTests

logger = logging.getLogger(__name__)

#pylint: disable=line-too-long


@requests_mock.Mocker()
class Tests(BaseTests):

    maxDiff = None

    def test_sanitize_html(self, mock):
        raw_html = """<![CDATA[<p>God&#39;s Debris: The Complete Works, Amazon <a href="https://tinyurl.com/GodsDebrisCompleteWorks">https://tinyurl.com/GodsDebrisCompleteWorks</a></p>
<p><strong>Find my &quot;extra&quot; content on Locals: </strong><a href="https://ScottAdams.Locals.com"><strong>https://ScottAdams.Locals.com</strong></a></p>
<p><strong>Content:</strong></p>
<p>Politics, Ultra-Processed Food, Kamala Harris, Trump Pirate Ship, Green Energy Progress, Warren Buffett BofA Stock, General McMaster, Jack Smith New indictments, Telegram Backdoor Battle, Pavel Durov, RFK Jr. State Ballot Battles, Scott Jennings, Border Half-Czar Harris, Voter Roll Programmed Cheating, Calley Means, Banned Food Chemicals, Government Size Reduction, National Debt Crisis, Scott Adams</p>
<p>~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~</p>
<p>If you would like to enjoy this same content plus bonus content from Scott Adams, including <em><strong>micro-lessons on lots of useful topics</strong></em><em> </em>to build your talent stack, please see <a href="http://scottadams.locals.com/">scottadams.locals.com</a> for full access to that secret treasure.</p>
<p><br></p>]]>"""
        expected_html = """<p>God&#39;s Debris: The Complete Works, Amazon <a href="https://tinyurl.com/GodsDebrisCompleteWorks">https://tinyurl.com/GodsDebrisCompleteWorks</a></p>
<p><strong>Find my &quot;extra&quot; content on Locals: </strong><a href="https://ScottAdams.Locals.com"><strong>https://ScottAdams.Locals.com</strong></a></p>
<p><strong>Content:</strong></p>
<p>Politics, Ultra-Processed Food, Kamala Harris, Trump Pirate Ship, Green Energy Progress, Warren Buffett BofA Stock, General McMaster, Jack Smith New indictments, Telegram Backdoor Battle, Pavel Durov, RFK Jr. State Ballot Battles, Scott Jennings, Border Half-Czar Harris, Voter Roll Programmed Cheating, Calley Means, Banned Food Chemicals, Government Size Reduction, National Debt Crisis, Scott Adams</p>
<p>~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~</p>
<p>If you would like to enjoy this same content plus bonus content from Scott Adams, including <em><strong>micro-lessons on lots of useful topics</strong></em><em> </em>to build your talent stack, please see <a href="http://scottadams.locals.com/">scottadams.locals.com</a> for full access to that secret treasure.</p>
<p><br></p>"""
        logger.info('Expected HTML: %s', expected_html)
        sanitized_html = sanitize_html(expected_html)
        logger.info('Actual HTML: %s', sanitized_html)
        self.assertEqual(expected_html, sanitized_html)

    def test_unescape_double_escaped_html(self, mock):
        """Test that double-escaped HTML tags are properly unescaped."""
        # Double-escaped HTML (what some feeds incorrectly send)
        double_escaped = '&lt;p&gt;Hello &lt;strong&gt;world&lt;/strong&gt;&lt;/p&gt;'
        expected = '<p>Hello <strong>world</strong></p>'
        result = unescape_double_escaped_html(double_escaped)
        self.assertEqual(expected, result)

    def test_unescape_double_escaped_html_with_links(self, mock):
        """Test double-escaped HTML with anchor tags."""
        double_escaped = '&lt;p&gt;Check out &lt;a href="https://example.com"&gt;this link&lt;/a&gt;&lt;/p&gt;'
        expected = '<p>Check out <a href="https://example.com">this link</a></p>'
        result = unescape_double_escaped_html(double_escaped)
        self.assertEqual(expected, result)

    def test_unescape_normal_html_unchanged(self, mock):
        """Test that normal HTML is not modified."""
        normal_html = '<p>Hello <strong>world</strong></p>'
        result = unescape_double_escaped_html(normal_html)
        self.assertEqual(normal_html, result)

    def test_unescape_empty_string(self, mock):
        """Test that empty string is handled."""
        self.assertEqual('', unescape_double_escaped_html(''))
        self.assertIsNone(unescape_double_escaped_html(None))

    def test_sanitize_html_with_double_escaped_input(self, mock):
        """Test that sanitize_html properly handles double-escaped input."""
        # This simulates what a broken feed might send
        double_escaped = '&lt;p&gt;Hello &lt;strong&gt;world&lt;/strong&gt;&lt;/p&gt;'
        # After sanitize_html, it should be proper HTML (with allowed tags preserved)
        result = sanitize_html(double_escaped)
        self.assertIn('<p>', result)
        self.assertIn('<strong>', result)
        self.assertNotIn('&lt;p&gt;', result)
