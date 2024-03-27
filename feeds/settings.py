from django.conf import settings

FEEDS_POST_SLUG_MAXLENGTH = settings.FEEDS_POST_SLUG_MAXLENGTH = getattr(settings, 'FEEDS_POST_SLUG_MAXLENGTH', 2000)
