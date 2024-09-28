from django.conf import settings

FEEDS_POST_SLUG_MAXLENGTH = settings.FEEDS_POST_SLUG_MAXLENGTH = getattr(settings, 'FEEDS_POST_SLUG_MAXLENGTH', 2000)

FEEDS_USER_AGENT = settings.FEEDS_USER_AGENT = getattr(settings, 'FEEDS_USER_AGENT', 'django-feed-reader')

server = "Unknown Server"
for h in settings.ALLOWED_HOSTS:
    if "." in h:
        server = "http://" + h
        break

FEEDS_SERVER = settings.FEEDS_SERVER = getattr(settings, 'FEEDS_SERVER', server)

default_allowed_tags = ['em', 'ol', 'ul', 'acronym', 'strong', 'blockquote', 'abbr', 'i', 'b', 'a', 'li', 'code', 'img', 'p', 'br', 'div']

FEEDS_ALLOWED_TAGS = settings.FEEDS_ALLOWED_TAGS = getattr(settings, 'FEEDS_ALLOWED_TAGS', default_allowed_tags)

default_allowed_attributes = {
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'a': ['href'],
}

FEEDS_ALLOWED_ATTRIBUTES = settings.FEEDS_ALLOWED_ATTRIBUTES = getattr(settings, 'FEEDS_ALLOWED_ATTRIBUTES', default_allowed_attributes)
