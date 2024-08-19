from django.conf import settings

FEEDS_POST_SLUG_MAXLENGTH = settings.FEEDS_POST_SLUG_MAXLENGTH = getattr(settings, 'FEEDS_POST_SLUG_MAXLENGTH', 2000)

FEEDS_USER_AGENT = settings.FEEDS_USER_AGENT = getattr(settings, 'FEEDS_USER_AGENT', 'django-feed-reader')

server = "Unknown Server"
for h in settings.ALLOWED_HOSTS:
    if "." in h:
        server = "http://" + h
        break

FEEDS_SERVER = settings.FEEDS_SERVER = getattr(settings, 'FEEDS_SERVER', server)
