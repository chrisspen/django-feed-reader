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
        'source',
    )

    search_fields = ('title',)

    readonly_fields = (
        'enclosures_link',
    )

    def enclosures_link(self, obj=None):
        if not obj or not obj.id:
            return ''
        qs = obj.enclosures.all()
        return mark_safe('<a href="/admin/feeds/enclosure/?post__id=%i" target="_blank">%i Enclosures</a>' % (obj.id, qs.count()))
    enclosures_link.short_description = 'enclosures'

class EnclosureAdmin(admin.ModelAdmin):

    raw_id_fields = ('post',)

    list_display = ('href', 'type', 'length')

admin.site.register(models.Source, SourceAdmin)
admin.site.register(models.Post, PostAdmin)
admin.site.register(models.Enclosure, EnclosureAdmin)
admin.site.register(models.WebProxy)
