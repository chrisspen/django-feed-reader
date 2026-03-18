from django.utils import timezone

from feeds.models import Post, Source

from .base import BaseTests


class Tests(BaseTests):

    def test_new_post_sets_db_timestamps(self):
        source = Source.objects.create(name='test source', feed_url=self.BASE_URL, interval=0)

        before = timezone.now()
        post = Post.objects.create(
            source=source,
            title='Test title',
            body='Test body',
            guid='guid-1',
            index=1,
        )
        after = timezone.now()

        self.assertIsNotNone(post.created_on)
        self.assertIsNotNone(post.updated_on)
        self.assertGreaterEqual(post.created_on, before)
        self.assertLessEqual(post.created_on, after)
        self.assertGreaterEqual(post.updated_on, before)
        self.assertLessEqual(post.updated_on, after)

    def test_existing_post_update_preserves_null_created_on(self):
        source = Source.objects.create(name='test source', feed_url=self.BASE_URL, interval=0)
        post = Post.objects.create(
            source=source,
            title='Test title',
            body='Test body',
            guid='guid-2',
            index=2,
        )
        Post.objects.filter(pk=post.pk).update(created_on=None, updated_on=None)

        post.refresh_from_db()
        post.title = 'Updated title'
        post.save()
        post.refresh_from_db()

        self.assertIsNone(post.created_on)
        self.assertIsNotNone(post.updated_on)
