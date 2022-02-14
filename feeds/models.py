# import time
import datetime
from urllib.parse import urlencode
import logging
# import sys
# import email

from django.db import models
from django.db.models import Max
from django.utils.timezone import utc
from django.utils.text import slugify


class SourceManager(models.Manager):

    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class Source(models.Model):

    objects = SourceManager()

    # This is an actual feed that we poll
    name = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(max_length=255, blank=True, null=True, unique=True)
    site_url = models.CharField(max_length=1000, blank=True, null=True)
    feed_url = models.CharField(max_length=1000)
    image_url = models.CharField(max_length=1000, blank=True, null=True)

    description = models.TextField(null=True, blank=True)

    last_polled = models.DateTimeField(max_length=255, blank=True, null=True)
    due_poll = models.DateTimeField(default=datetime.datetime(1900, 1, 1)) # default to distant past to put new sources to front of queue
    etag = models.CharField(max_length=255, blank=True, null=True)
    last_modified = models.CharField(max_length=255, blank=True, null=True) # just pass this back and forward between server and me , no need to parse

    last_result = models.CharField(max_length=255, blank=True, null=True)
    interval = models.PositiveIntegerField(default=400)
    last_success = models.DateTimeField(null=True, default=datetime.datetime(1900, 1, 1))
    last_change = models.DateTimeField(null=True, default=datetime.datetime(1900, 1, 1))
    live = models.BooleanField(default=True)
    status_code = models.PositiveIntegerField(default=0)
    last_302_url = models.CharField(max_length=1000, null=True, blank=True)
    last_302_start = models.DateTimeField(null=True, blank=True)

    max_index = models.IntegerField(default=0)

    num_subs = models.IntegerField(default=1)

    is_cloudflare = models.BooleanField(default=False)

    last_created = models.DateTimeField(blank=True, null=True, help_text='Datetime of most recent post.')

    def natural_key(self):
        return (self.slug,)

    def __str__(self):
        return self.display_name

    @property
    def best_link(self):
        #the html link else hte feed link
        if self.site_url is None or self.site_url == '':
            return self.feed_url
        return self.site_url

    @property
    def display_name(self):
        if self.name is None or self.name == "":
            return self.best_link
        return self.name

    @property
    def garden_style(self):

        if not self.live:
            css = "background-color:#ccc;"
        elif self.last_change is None or self.last_success is None:
            css = "background-color:#D00;color:white"
        else:
            dd = datetime.datetime.utcnow().replace(tzinfo=utc) - self.last_change

            days = int(dd.days / 2)

            col = 255 - days
            if col < 0: col = 0

            css = "background-color:#ff%02x%02x" % (col, col)

            if col < 128:
                css += ";color:white"

        return css

    @property
    def health_box(self):

        if not self.live:
            css = "#ccc;"
        elif self.last_change is None or self.last_success is None:
            css = "#F00;"
        else:
            dd = datetime.datetime.utcnow().replace(tzinfo=utc) - self.last_change

            days = int(dd.days / 2)

            red = days
            if red > 255:
                red = 255

            green = 255 - days
            if green < 0:
                green = 0

            css = "#%02x%02x00" % (red, green)

        return css

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify((self.name or '').strip())
        super().save(*args, **kwargs)

        agg = self.posts.all().aggregate(Max('created'))
        if agg:
            self.last_created = agg['created__max']
            type(self).objects.filter(id=self.id).update(last_created=self.last_created)


class PostManager(models.Manager):

    def get_by_natural_key(self, guid, *args):
        source = Source.objects.get_by_natural_key(*args)
        return self.get(guid=guid, source=source)


class Post(models.Model):

    # an entry in a feed

    objects = PostManager()

    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='posts')
    title = models.TextField(blank=True)
    slug = models.SlugField(max_length=2000, blank=True, null=True)
    body = models.TextField()
    link = models.CharField(max_length=512, blank=True, null=True)
    found = models.DateTimeField(auto_now_add=True)
    created = models.DateTimeField(db_index=True, auto_now_add=True)
    guid = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    author = models.CharField(max_length=255, blank=True, null=True)
    index = models.IntegerField(db_index=True)
    image_url = models.CharField(max_length=2000, blank=True, null=True)

    subtitle_href = models.URLField(max_length=1000, blank=True, null=True)
    subtitle_lang = models.CharField(max_length=50, blank=True, null=True)
    subtitle_type = models.CharField(max_length=50, blank=True, null=True)

    def natural_key(self):
        return (self.guid,) + self.source.natural_key()

    natural_key.dependencies = ['feeds.source']

    @property
    def title_url_encoded(self):
        try:
            ret = urlencode({"X": self.title})
            if len(ret) > 2: ret = ret[2:]
        except:
            logging.info("Failed to url encode title of post %s.", self.id)
            ret = ""

    def __str__(self):
        return "%s: post %d, %s" % (self.source.display_name, self.index, self.title)

    @property
    def recast_link(self):
        return "/post/%d/" % self.id

    class Meta:
        ordering = ["index"]
        unique_together = (
            ('source', 'slug'),
            ('source', 'guid'),
        )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify((self.title or '').strip())
        print('slug:', len(self.slug))
        print('guid:', len(self.guid or ''))
        print('author:', len(self.author or ''))
        print('image_url:', len(self.image_url or ''))
        super().save(*args, **kwargs)


class EnclosureManager(models.Manager):

    def get_by_natural_key(self, length, *args):
        post = Post.objects.get_by_natural_key(*args)
        return self.get(length=length, post=post)


class Enclosure(models.Model):

    objects = EnclosureManager()

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='enclosures')
    length = models.IntegerField(default=0)
    href = models.CharField(max_length=2000)
    type = models.CharField(max_length=256)

    def natural_key(self):
        # Length is a better predictor of uniqueness than href because href changes sometimes due to tracker prefixes.
        # Where as it's extremely unlikely two different enclosures under a single post have identical lengths.
        return (self.length,) + self.post.natural_key()

    natural_key.dependencies = ['feeds.post']

    @property
    def recast_link(self):
        return "/enclosure/%d/" % self.id


class MediaContent(models.Model):
    """
    Stores data contained in the <media:content> tags.
    """

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media_content')

    url = models.URLField(max_length=1000, blank=False, null=False)

    content_type = models.CharField(max_length=50, blank=False, null=False)

    duration = models.IntegerField(blank=True, null=True, help_text='Duration of media in seconds.')

    class Meta:
        unique_together = (
            ('post', 'url'),
        )

    def natural_key(self):
        return (self.url,) + self.post.natural_key()

    natural_key.dependencies = ['feeds.post']


class WebProxy(models.Model):
    # this class if for Cloudflare avoidance and contains a list of potential
    # web proxies that we can try, scraped from the internet
    address = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = 'web proxies'

    def __str__(self):
        return "Proxy:{}".format(self.address)
