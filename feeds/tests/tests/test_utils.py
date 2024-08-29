import logging
import requests_mock

from feeds.utils import sanitize_html

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
