from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import reverse

# Register your models here.
from feeds import models

class SourceAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'posts_link',
        'live',
    )

    list_filter = (
        'live',
    )

    readonly_fields = (
        'posts_link',
        'last_created',
    )

    search_fields = (
        'name',
    )

    prepopulated_fields = {"slug": ("name",)}

    def posts_link(self, obj=None):
        if not obj or not obj.id:
            return ''
        qs = obj.posts.all()
        url = reverse('admin:feeds_post_changelist')
        # return mark_safe('<a href="/admin/feeds/post/?source__id=%i" target="_blank">%i Posts</a>' % (obj.id, qs.count()))
        return mark_safe('<a href="%s?source__id=%i" target="_blank">%i Posts</a>' % (url, obj.id, qs.count()))
    posts_link.short_description = 'posts'


class PostAdmin(admin.ModelAdmin):

    raw_id_fields = ('source',)

    prepopulated_fields = {"slug": ("title",)}

    list_display = ('title', 'source', 'created', 'guid', 'author')

    list_filter = (
        # 'source',
    )

    search_fields = ('title',)

    readonly_fields = (
        'enclosures_link',
        'media_content_link',
        'subtitle_href',
        'subtitle_lang',
        'subtitle_type',
    )

    def lookup_allowed(self, request, model_admin):
        return True

    def enclosures_link(self, obj=None):
        if not obj or not obj.id:
            return ''
        qs = obj.enclosures.all()
        return mark_safe('<a href="/admin/feeds/enclosure/?post__id=%i" target="_blank">%i Enclosures</a>' % (obj.id, qs.count()))
    enclosures_link.short_description = 'enclosures'

    def media_content_link(self, obj=None):
        if not obj or not obj.id:
            return ''
        qs = obj.media_content.all()
        return mark_safe('<a href="/admin/feeds/mediacontent/?post__id=%i" target="_blank">%i Media Content</a>' % (obj.id, qs.count()))
    media_content_link.short_description = 'media content'


class EnclosureAdmin(admin.ModelAdmin):

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
