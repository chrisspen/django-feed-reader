"""
Tests for feeds admin functionality.
"""
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from feeds import models
from feeds.admin import SourceAdmin, EnclosureAdmin, MediaContentAdmin


class AdminImportTests(TestCase):
    """Test that admin imports work correctly."""

    def test_source_admin_get_queryset_uses_count(self):
        """
        Test that SourceAdmin.get_queryset() works correctly.

        This tests for a regression where `from feeds import models` was
        shadowing `from django.db import models`, causing models.Count
        to fail with AttributeError.
        """
        site = AdminSite()
        admin = SourceAdmin(models.Source, site)

        factory = RequestFactory()
        request = factory.get('/admin/feeds/source/')
        request.user = None

        # This should not raise AttributeError: module 'feeds.models' has no attribute 'Count'
        qs = admin.get_queryset(request)

        # Verify it returns a valid queryset
        self.assertIsNotNone(qs)

        # Verify the annotation is present
        self.assertIn('posts_count', qs.query.annotations)

    def test_enclosure_admin_lookup_allowed_accepts_related_lookup(self):
        site = AdminSite()
        admin = EnclosureAdmin(models.Enclosure, site)

        self.assertTrue(admin.lookup_allowed('post__id', '123'))

    def test_media_content_admin_lookup_allowed_accepts_related_lookup(self):
        site = AdminSite()
        admin = MediaContentAdmin(models.MediaContent, site)

        self.assertTrue(admin.lookup_allowed('post__id', '123'))
