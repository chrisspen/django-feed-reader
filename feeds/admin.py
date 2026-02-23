from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db import models

# Register your models here.
from feeds import models


class SourceAdmin(admin.ModelAdmin):

    show_full_result_count = False

    list_display = (
        'name',
        'posts_link',
        'live',
    )

    list_filter = ('live',)

    readonly_fields = (
        'posts_link',
        'last_created',
        'lucene_index_actual',
        'uuid',
    )

    search_fields = (
        'name',
        'uuid',
    )

    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('chunking_options').annotate(posts_count=models.Count('posts'))

    def lookup_allowed(self, lookup, value, request=None):
        return True

    def posts_link(self, obj=None):
        if not obj or not obj.id:
            return ''
        url = reverse('admin:feeds_post_changelist')
        count = getattr(obj, 'posts_count', None)
        if count is None:
            count = obj.posts.count()
        return mark_safe(f'<a href="{url}?source_id={obj.id}" target="_blank">{count} Posts</a>')

    posts_link.short_description = 'posts'


class PostAdmin(admin.ModelAdmin):

    show_full_result_count = False

    raw_id_fields = ('source',)

    prepopulated_fields = {"slug": ("title",)}

    list_display = ('title', 'source', 'created', 'guid', 'author')

    list_filter = (
        # 'source',
    )

    search_fields = (
        'title',
        'uuid',
    )

    readonly_fields = (
        'enclosures_link',
        'media_content_link',
        'subtitle_href',
        'subtitle_lang',
        'subtitle_type',
        'lucene_index_actual',
        'uuid',
    )

    def lookup_allowed(self, lookup, value, request=None):
        return True

    def enclosures_link(self, obj=None):
        if not obj or not obj.id:
            return ''
        qs = obj.enclosures.all()
        return mark_safe(f'<a href="/admin/feeds/enclosure/?post__id={obj.id}" target="_blank">{qs.count()} Enclosures</a>')

    enclosures_link.short_description = 'enclosures'

    def media_content_link(self, obj=None):
        if not obj or not obj.id:
            return ''
        qs = obj.media_content.all()
        return mark_safe(f'<a href="/admin/feeds/mediacontent/?post__id={obj.id}" target="_blank">{qs.count()} Media Content</a>')

    media_content_link.short_description = 'media content'


class EnclosureAdmin(admin.ModelAdmin):

    show_full_result_count = False

    raw_id_fields = ('post',)

    list_display = ('href', 'type', 'length')

    def lookup_allowed(self, request, model_admin):
        return True


class MediaContentAdmin(admin.ModelAdmin):

    raw_id_fields = ('post',)

    list_display = ('url', 'content_type', 'duration')

    readonly_fields = (
        'post',
        'url',
        'content_type',
        'duration',
    )

    def lookup_allowed(self, request, model_admin):
        return True


admin.site.register(models.Source, SourceAdmin)
admin.site.register(models.Post, PostAdmin)
admin.site.register(models.Enclosure, EnclosureAdmin)
admin.site.register(models.MediaContent, MediaContentAdmin)
admin.site.register(models.WebProxy)
