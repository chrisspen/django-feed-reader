# import os
import time
import datetime
# from urllib.parse import urljoin
import hashlib
from random import choice
import logging
import json

from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.db.utils import IntegrityError

from feeds.models import Source, Enclosure, Post, WebProxy, MediaContent

import feedparser

# from bs4 import BeautifulSoup

import requests

import pyrfc3339


class NullOutput:
    # little class for when we have no outputter
    def write(self, str): # pylint: disable=redefined-builtin
        pass


def _customize_sanitizer(fp):


    bad_attributes = [
        "align",
        "valign",
        "hspace"
    ]

    for item in bad_attributes:
        try:
            if item in fp._HTMLSanitizer.acceptable_attributes:
                fp._HTMLSanitizer.acceptable_attributes.remove(item)
        except Exception:
            logging.debug("Could not remove %s", item)


def get_agent(source_feed):

    if source_feed.is_cloudflare:
        agent = random_user_agent()
        logging.info("Using agent: %s", agent)
    else:
        agent = "{user_agent} (+{server}; Updater; {subs} subscribers)".format(
            user_agent=settings.FEEDS_USER_AGENT, server=settings.FEEDS_SERVER, subs=source_feed.num_subs)

    return agent


def random_user_agent():
    return choice([
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)",
        "Mozilla/5.0 (iPad; CPU OS 8_4_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H321 Safari/600.1.4",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1",
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (Linux; Android 5.0; SAMSUNG SM-N900 Build/LRX21V) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/2.1 Chrome/34.0.1847.76 "\
        "Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 6.0.1; SAMSUNG SM-G570Y Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/4.0 Chrome/44.0.2403.133 "\
        "Mobile Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0"
    ])



def fix_relative(html, url):

    """ this is fucking cheesy """


    try:
        base = "/".join(url.split("/")[:3])

        html = html.replace("src='//", "src='http://")
        html = html.replace('src="//', 'src="http://')


        html = html.replace("src='/", "src='%s/" % base)
        html = html.replace('src="/', 'src="%s/' % base)

    except Exception as ex:
        pass

    return html


def update_feeds(max_feeds=3, output=NullOutput(), sources=None, force=False):

    if sources is None:
        todo = Source.objects.filter(Q(due_poll__lt=timezone.now()) & Q(live=True))
    else:
        todo = sources

    logging.info("Queue size is %i.", todo.count())

    sources = todo.order_by("due_poll")[:max_feeds]

    logging.info("Processing %d.", sources.count())

    for src in sources:
        read_feed(src, output, force=force)

    # kill shit proxies

    WebProxy.objects.filter(address='X').delete()


def read_feed(source_feed, output=NullOutput(), force=False):

    old_interval = source_feed.interval


    was302 = False

    logging.info("\n------------------------------\n")

    source_feed.last_polled = timezone.now()

    agent = get_agent(source_feed)

    headers = {"User-Agent": agent}

    proxies = {}
    proxy = None
    if source_feed.is_cloudflare:
        try:
            proxy = get_proxy(output)
            if proxy.address != "X":
                proxies = {
                  'http': "http://" + proxy.address,
                  'https': "https://" + proxy.address,
                }
        except Exception:
            pass

    if not force:
        if source_feed.etag:
            headers["If-None-Match"] = str(source_feed.etag)
        if source_feed.last_modified:
            headers["If-Modified-Since"] = str(source_feed.last_modified)

    logging.info("Fetching %s.", source_feed.feed_url)

    ret = None
    try:
        ret = requests.get(source_feed.feed_url, headers=headers, allow_redirects=False, timeout=20, proxies=proxies)
        source_feed.status_code = ret.status_code
        source_feed.last_result = "Unhandled Case"
        logging.info('Response: %s', str(ret))
    except Exception as ex:
        logging.exception("Fetch feed error from source %s url %s: %s", source_feed.id, source_feed.feed_url, ex)
        source_feed.last_result = ("Fetch error:" + str(ex))[:255]
        source_feed.status_code = 0


        if proxy:
            source_feed.lastResult = "Proxy failed. Next retry will use new proxy"
            source_feed.status_code = 1  # this will stop us increasing the interval

            logging.info("Burning the proxy.")
            proxy.delete()
            source_feed.interval /= 2



    if ret is None and source_feed.status_code == 1:   # er ??
        pass
    elif ret is None or source_feed.status_code == 0:
        source_feed.interval += 120
    elif ret.status_code < 200 or ret.status_code >= 500:
        #errors, impossible return codes
        source_feed.interval += 120
        source_feed.last_result = "Server error fetching feed (%d)" % ret.status_code
    elif ret.status_code == 404:
        #not found
        source_feed.interval += 120
        source_feed.last_result = "The feed could not be found"
    elif ret.status_code == 403 or ret.status_code == 410: #Forbidden or gone
        if "Cloudflare" in ret.text or ("Server" in ret.headers and "cloudflare" in ret.headers["Server"]):
            if source_feed.is_cloudflare and proxy is not None:
                # we are already proxied - this proxy on cloudflare's shit list too?
                proxy.delete()
                logging.info("Proxy seems to also be blocked, burning.")
                source_feed.interval /= 2
                source_feed.lastResult = "Proxy kind of worked but still got cloudflared."
            else:
                source_feed.is_cloudflare = True
                source_feed.last_result = "Blocked by Cloudflare (grr)"
        else:
            source_feed.last_result = "Feed is no longer accessible."
            source_feed.live = False


    elif ret.status_code >= 400 and ret.status_code < 500:
        #treat as bad request
        source_feed.live = False
        source_feed.last_result = "Bad request (%d)" % ret.status_code
    elif ret.status_code == 304:
        #not modified
        source_feed.interval += 10
        source_feed.last_result = "Not modified"
        source_feed.last_success = timezone.now()

        if source_feed.last_success and (timezone.now() - source_feed.last_success).days > 7:
            source_feed.last_result = "Clearing etag/last modified due to lack of changes"
            source_feed.etag = None
            source_feed.last_modified = None

    elif ret.status_code == 301 or ret.status_code == 308: #permenant redirect
        new_url = ""
        try:
            if "Location" in ret.headers:
                new_url = ret.headers["Location"]

                if new_url[0] == "/":
                    #find the domain from the feed

                    base = "/".join(source_feed.feed_url.split("/")[:3])


                    new_url = base + new_url


                source_feed.feed_url = new_url

                source_feed.last_result = "Moved"
            else:
                source_feed.last_result = "Feed has moved but no location provided"
        except Exception as Ex:
            logging.info("\nError redirecting.")
            source_feed.last_result = "Error redirecting feed to " + new_url
    elif ret.status_code == 302 or ret.status_code == 303 or ret.status_code == 307: #Temporary redirect
        new_url = ""
        was302 = True
        try:
            new_url = ret.headers["Location"]

            if new_url[0] == "/":
                #find the domain from the feed
                start = source_feed.feed_url[:8]
                end = source_feed.feed_url[8:]
                if end.find("/") >= 0:
                    end = end[:end.find("/")]

                new_url = start + end + new_url


            ret = requests.get(new_url, headers=headers, allow_redirects=True, timeout=20)
            source_feed.status_code = ret.status_code
            source_feed.last_result = "Temporary Redirect to " + new_url

            if source_feed.last_302_url == new_url:
                #this is where we 302'd to last time
                td = timezone.now() - source_feed.last_302_start
                if td.days > 60:
                    source_feed.feed_url = new_url
                    source_feed.last_302_url = " "
                    source_feed.last_302_start = None
                    source_feed.last_result = "Permanent Redirect to " + new_url
                else:
                    source_feed.last_result = "Temporary Redirect to " + new_url + " since " + source_feed.last_302_start.strftime("%d %B")

            else:
                source_feed.last_302_url = new_url
                source_feed.last_302_start = timezone.now()

                source_feed.last_result = "Temporary Redirect to " + new_url + " since " + source_feed.last_302_start.strftime("%d %B")


        except Exception as ex:
            source_feed.last_result = "Failed Redirection to " + new_url +  " " + str(ex)
            source_feed.interval += 60

    #NOT ELIF, WE HAVE TO START THE IF AGAIN TO COPE WTIH 302
    #now we are not following redirects 302,303 and so forth are going to fail here, but what the hell :)
    if ret and ret.status_code >= 200 and ret.status_code < 300:

        # great!
        ok = True
        changed = False


        if was302:
            source_feed.etag = None
            source_feed.last_modified = None
        else:
            try:
                source_feed.etag = ret.headers["etag"]
            except Exception as ex:
                source_feed.etag = None
            try:
                source_feed.last_modified = ret.headers["Last-Modified"]
            except Exception as ex:
                source_feed.last_modified = None

        logging.info("Etag:%s", source_feed.etag)
        logging.info("Last Mod:%s", source_feed.last_modified)

        content_type = "Not Set"
        if "Content-Type" in ret.headers:
            content_type = ret.headers["Content-Type"]
        logging.info('content_type: %s', content_type)

        (ok, changed) = import_feed(source_feed=source_feed, feed_body=ret.content, content_type=content_type, output=output)
        if ok and changed:
            logging.info('OK-changed')
            source_feed.interval /= 2
            source_feed.last_result = " OK (updated)" #and temporary redirects
            source_feed.last_change = timezone.now()
        elif ok:
            logging.info('OK-unchanged')
            source_feed.last_result = "OK"
            source_feed.interval += 20 # we slow down feeds a little more that don't send headers we can use
        else:
            logging.info('BAD')
            source_feed.interval += 120

    if source_feed.interval < 60:
        source_feed.interval = 60 # no less than 1 hour
    if source_feed.interval > (60 * 24):
        source_feed.interval = (60 * 24) # no more than a day

    logging.info("Updating source_feed.interval from %d to %d.", old_interval, source_feed.interval)
    td = datetime.timedelta(minutes=source_feed.interval)
    source_feed.due_poll = timezone.now() + td
    source_feed.save()


def import_feed(source_feed, feed_body, content_type, output=NullOutput()):


    ok = False
    changed = False

    if "xml" in content_type or "html" in content_type or feed_body[0:1] == b"<":
        logging.info('Parsing XML...')
        (ok, changed) = parse_feed_xml(source_feed, feed_body, output)
    elif "json" in content_type or feed_body[0:1] == b"{":
        logging.info('Parsing JSON...')
        (ok, changed) = parse_feed_json(source_feed, str(feed_body, "utf-8"), output)
    else:
        logging.info('Unknown feed type: %s', content_type)
        ok = False
        source_feed.last_result = "Unknown Feed Type: " + content_type

    if ok and changed:
        source_feed.last_result = " OK (updated)" #and temporary redirects
        source_feed.last_change = timezone.now()

        idx = source_feed.max_index
        # give indices to posts based on created date
        posts = Post.objects.filter(Q(source=source_feed) & Q(index=0)).order_by("created")
        for p in posts:
            idx += 1
            p.index = idx
            p.save()

        source_feed.max_index = idx

    return (ok, changed)



def parse_feed_xml(source_feed, feed_content, output):

    ok = True
    changed = False

    try:

        _customize_sanitizer(feedparser)
        f = feedparser.parse(feed_content) #need to start checking feed parser errors here
        entries = f['entries']
        if entries:
            source_feed.last_success = timezone.now() #in case we start auto unsubscribing long dead feeds
        else:
            source_feed.last_result = "Feed is empty"
            ok = False

    except Exception as ex:
        source_feed.last_result = "Feed Parse Error"
        entries = []
        ok = False

    if ok:
        try:
            if not source_feed.name:
                source_feed.name = f.feed.title
        except Exception as ex:
            pass

        try:
            source_feed.site_url = f.feed.link
        except Exception as ex:
            pass


        try:
            source_feed.image_url = f.feed.image.href
        except:
            pass


        # either of these is fine, prefer description over summary
        # also feedparser will give us itunes:summary etc if there
        try:
            source_feed.description = f.feed.summary
        except:
            pass

        try:
            source_feed.description = f.feed.description
        except:
            pass


        #logging.info(entries)
        entries.reverse() # Entries are typically in reverse chronological order - put them in right order
        for e in entries:

            # we are going to take the longest
            body = ""

            if hasattr(e, "content"):
                for c in e.content:
                    if len(c.value) > len(body):
                        body = c.value

            if hasattr(e, "summary"):
                if len(e.summary) > len(body):
                    body = e.summary

            if hasattr(e, "summary_detail"):
                if len(e.summary_detail.value) > len(body):
                    body = e.summary_detail.value

            if hasattr(e, "description"):
                if len(e.description) > len(body):
                    body = e.description


            body = fix_relative(body, source_feed.site_url)

            guid = None
            try:
                guid = e.guid
            except Exception as ex:
                try:
                    guid = e.link
                except Exception as ex:
                    m = hashlib.md5()
                    m.update(body.encode("utf-8"))
                    guid = m.hexdigest()

            post_defaults = {}

            try:
                post_defaults['title'] = e.title
            except (AttributeError, KeyError):
                post_defaults['title'] = ""

            try:
                post_defaults['link'] = e.link
            except (AttributeError, KeyError):
                post_defaults['link'] = ''

            try:
                post_defaults['image_url'] = e.image.href
            except (AttributeError, KeyError):
                pass

            force_set_created = True
            try:
                logging.info('Raw created date: %s', e.published_parsed)
                post_defaults['created'] = datetime.datetime.fromtimestamp(time.mktime(e.published_parsed)).replace(tzinfo=timezone.utc)
                logging.info('Normalized created date: %s', post_defaults['created'])
            except Exception as ex:
                force_set_created = False
                logging.exception("Unable to parse published timestamp.")
                post_defaults['created'] = timezone.now()

            try:
                post_defaults['author'] = e.author
            except (AttributeError, KeyError):
                post_defaults['author'] = ""

            post_defaults.setdefault('found', timezone.now())
            post_defaults.setdefault('index', 0)
            post_defaults.setdefault('body', ' ')

            logging.info('Getting or creating post %s %s for source %s...', post_defaults['title'], guid, source_feed)
            try:
                p, changed = Post.objects.get_or_create(source=source_feed, guid=guid, defaults=post_defaults)
                if force_set_created:
                    p.created = post_defaults['created']
                p.save()
            except IntegrityError:
                # If this happens, it usually means some idiot changed the non-editable permalink for their post after we initially parsed it,
                # but left the title the same, resulting in a post with a duplicate slug but different GUID.
                # Since we've already parsed this post, and have already loaded its enclosures, we'll ignore this revised post because the change
                # is likely irrelevant.
                continue

            seen_files = []
            for ee in list(p.enclosures.all()):
                # check existing enclosure is still there
                found_enclosure = False
                for pe in e["enclosures"]:
                    enc_href = pe.get('href') or pe.get('url')
                    if enc_href == ee.href and ee.href not in seen_files:
                        found_enclosure = True
                        ee.length = int(pe.get("length", None) or 0)
                        typ = pe.get("type", None) or "audio/mpeg"  # we are assuming podcasts here but that's probably not safe
                        ee.type = typ
                        ee.save()
                        break

                # DANGEROUS! If there's a glitch in the feed that temporarily removes all enclosures, this will delete everything!
                # if not found_enclosure:
                    # ee.delete()

                seen_files.append(ee.href)

            for pe in e["enclosures"]:
                enc_href = pe.get('href') or pe.get('url')
                if enc_href and enc_href not in seen_files and not p.enclosures.all().exists():
                    length = int(pe.get("length") or 0)
                    typ = pe.get("type") or "audio/mpeg"
                    ee = Enclosure(post=p, href=enc_href, length=length, type=typ)
                    ee.save()

            if 'media_subtitle' in e:
                p.subtitle_href = e['media_subtitle'].get('href')
                p.subtitle_lang = e['media_subtitle'].get('lang')
                p.subtitle_type = e['media_subtitle'].get('type')

            try:
                p.body = body
                p.save()
            except Exception as ex:
                logging.exception('Unable to save post body.')

            if 'media_content' in e:
                for media_dict in e['media_content']:
                    media_url = media_dict.get('url') or None
                    if not media_url:
                        continue
                    media_type = media_dict.get('type') or None
                    if not media_type:
                        continue
                    try:
                        media_duration = int(float(media_dict.get('duration') or None))
                    except (ValueError, TypeError):
                        media_duration = None
                    MediaContent.objects.get_or_create(post=p, url=media_url, content_type=media_type, defaults={'duration': media_duration})

            # If no primary enclosure but media content contains an mp3 or mp4, then simulate one.
            possible_enclosure_sources = p.media_content.filter(content_type__in=('video/mp4', 'audio/mpeg'))
            if not p.enclosures.all().exists() and possible_enclosure_sources.exists():
                media_source = possible_enclosure_sources.first()
                Enclosure.objects.get_or_create(post=p, href=media_source.url, type=media_source.content_type, defaults={'length': media_source.duration})

    return (ok, changed)


def parse_feed_json(source_feed, feed_content, output):

    ok = True
    changed = False

    try:
        f = json.loads(feed_content)
        entries = f['items']
        if entries:
            source_feed.last_success = timezone.now() #in case we start auto unsubscribing long dead feeds
        else:
            source_feed.last_result = "Feed is empty"
            source_feed.interval += 120
            ok = False

    except Exception as ex:
        source_feed.last_result = "Feed Parse Error"
        entries = []
        source_feed.interval += 120
        ok = False

    if ok:


        if "expired" in f and f["expired"]:
            # This feed says it is done
            # TODO: permanently disable
            # for now source_feed.interval to max
            source_feed.interval = (24*3*60)
            source_feed.last_result = "This feed has expired"
            return (False, False, source_feed.interval)

        try:
            source_feed.site_url = f["home_page_url"]
            if not source_feed.name:
                source_feed.name = f["title"]
        except Exception as ex:
            pass


        if "description" in f:
            _customize_sanitizer(feedparser)
            source_feed.description = feedparser._sanitizeHTML(f["description"], "utf-8", 'text/html')

        _customize_sanitizer(feedparser)
        if not source_feed.name:
            source_feed.name = feedparser._sanitizeHTML(source_feed.name, "utf-8", 'text/html')

        if "icon" in f:
            source_feed.image_url = f["icon"]

        entries.reverse() # Entries are typically in reverse chronological order - put them in right order
        for e in entries:
            body = " "
            if "content_text" in e:
                body = e["content_text"]
            if "content_html" in e:
                body = e["content_html"] # prefer html over text

            body = fix_relative(body, source_feed.site_url)

            try:
                guid = e["id"]
            except Exception as ex:
                try:
                    guid = e["url"]
                except Exception as ex:
                    m = hashlib.md5()
                    m.update(body.encode("utf-8"))
                    guid = m.hexdigest()

            try:
                p = Post.objects.filter(source=source_feed).filter(guid=guid)[0]
                logging.info("EXISTING: %s", guid)
            except Exception as ex:
                logging.info("Creating new post %s.", guid)
                p = Post(index=0, body=' ')
                p.found = timezone.now()
                changed = True
                p.source = source_feed

            try:
                title = e["title"]
            except Exception as ex:
                title = ""

            # borrow the RSS parser's sanitizer
            _customize_sanitizer(feedparser)
            body = feedparser._sanitizeHTML(body, "utf-8", 'text/html') # TODO: validate charset ??
            _customize_sanitizer(feedparser)
            title = feedparser._sanitizeHTML(title, "utf-8", 'text/html') # TODO: validate charset ??
            # no other fields are ever marked as |safe in the templates

            if "banner_image" in e:
                p.image_url = e["banner_image"]

            if "image" in e:
                p.image_url = e["image"]


            try:
                p.link = e["url"]
            except Exception as ex:
                p.link = ''

            p.title = title

            try:
                p.created = pyrfc3339.parse(e["date_published"])
            except Exception as ex:
                logging.exception('Unable to parse published date.')
                p.created = timezone.now()

            p.guid = guid
            try:
                p.author = e["author"]
            except Exception as ex:
                p.author = ""

            p.save()


            try:
                seen_files = []
                for ee in list(p.enclosures.all()):
                    # check existing enclosure is still there
                    found_enclosure = False
                    if "attachments" in e:
                        for pe in e["attachments"]:
                            if pe["url"] == ee.href and ee.href not in seen_files:
                                found_enclosure = True
                                ee.length = int(pe.get("size_in_bytes", None) or 0)
                                typ = pe.get("mime_type", None) or "audio/mpeg"
                                ee.type = typ
                                ee.save()
                                break

                    # DANGEROUS! This deletes everything if a glitch in the feed removes enclosures.
                    # if not found_enclosure:
                        # ee.delete()

                    seen_files.append(ee.href)

                if "attachments" in e:
                    for pe in e["attachments"]:
                        try:
                            # Since many RSS feeds embed trackers into their URL that constantly change, yet almost always only include a single enclosure,
                            # we'll only create a new enclosure when we see a new url if there are no enclosure records created yet.
                            # This is a most robust way of preventing logical duplicates due to tracker URL changes then by trying to predict and strip out
                            # all known tracker prefixes.
                            if pe["url"] not in seen_files and not p.enclosures.all().exists():
                                length = int(pe.get("size_in_bytes", None) or 0)
                                typ = pe.get("mime_type", None) or "audio/mpeg"
                                ee = Enclosure(post=p, href=pe["url"], length=length, type=typ)
                                ee.save()
                        except Exception as ex:
                            pass
            except Exception as ex:
                logging.exception("No enclosures")

            try:
                p.body = body
                p.save()
            except Exception as ex:
                logging.exception('Unable to save body A2.')

    return (ok, changed)


def test_feed(source, cache=False, output=NullOutput()):

    user_agent = get_agent(source)
    headers = {"User-Agent": user_agent} #identify ourselves and also stop our requests getting picked up by any cache

    if cache:
        if source.etag:
            headers["If-None-Match"] = str(source.etag)
        if source.last_modified:
            headers["If-Modified-Since"] = str(source.last_modified)
    else:
        headers["Cache-Control"] = "no-cache,max-age=0"
        headers["Pragma"] = "no-cache"

    output.write("\n" + str(headers))

    ret = requests.get(source.feed_url, headers=headers, allow_redirects=False, verify=False, timeout=20)

    output.write("\n\n")

    output.write(str(ret))

    output.write("\n\n")

    output.write(ret.text)


def get_proxy(out=NullOutput()):

    p = WebProxy.objects.first()

    if p is None:
        find_proxies(out)
        p = WebProxy.objects.first()

    out.write("Proxy: {}".format(str(p)))

    return p



def find_proxies(out=NullOutput()):

    logging.info("Looking for proxies.")

    try:
        req = requests.get("https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt", timeout=30)
        if req.status_code == 200:
            lst = req.text

            lst = lst.split("\n")

            # remove header
            lst = lst[4:]

            for item in lst:
                if ":" in item:
                    item = item.split(" ")[0]
                    WebProxy(address=item).save()

    except Exception as ex:
        logging.exception("Unable to scrape proxy.")

    if WebProxy.objects.count() == 0:
        # something went wrong.
        # to stop infinite loops we will insert duff proxys now
        for i in range(20):
            WebProxy(address="X").save()
        logging.info("No proxies found.")
