from django.contrib import admin

from .models import Comment, Follow, Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'group', 'pub_date', 'author')
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'description')
    search_fields = ('title',)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'text', 'author', 'created')
    list_filter = ('author',)


class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    list_filter = ('user', 'author')


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
