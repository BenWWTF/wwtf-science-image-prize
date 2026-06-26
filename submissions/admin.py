from django.contrib import admin
from django.utils.html import format_html
from .models import Submission, SubmissionImage


class SubmissionImageInline(admin.TabularInline):
    model = SubmissionImage
    extra = 0
    readonly_fields = ('order', 'title', 'method', 'description', 'scientific_context', 'preview')
    fields = ('order', 'preview', 'title', 'method', 'description', 'scientific_context')

    def preview(self, obj):
        if obj.file:
            return format_html('<img src="{}" style="max-height:120px;max-width:180px;border-radius:4px;">', obj.file.url)
        return '—'
    preview.short_description = 'Preview'


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'institution', 'position', 'research_field', 'image_count', 'created_at')
    list_filter = ('position', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'institution', 'research_field')
    readonly_fields = ('id', 'created_at', 'ip_address')
    inlines = [SubmissionImageInline]

    def image_count(self, obj):
        return obj.images.count()
    image_count.short_description = '# Images'


@admin.register(SubmissionImage)
class SubmissionImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'submission', 'order', 'method')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.file:
            return format_html('<img src="{}" style="max-height:300px;border-radius:4px;">', obj.file.url)
        return '—'
