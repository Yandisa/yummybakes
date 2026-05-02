from django.contrib import admin
from django.utils.html import format_html
from .models import Testimonial, GalleryImage, MenuItem, Order

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'is_approved', 'created_at')
    list_filter = ('is_approved',)
    search_fields = ('name', 'location', 'message')
    ordering = ('-created_at',)
    list_editable = ('is_approved',)
    date_hierarchy = 'created_at'


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80" height="auto" />', obj.image.url)
        return "-"
    thumbnail.short_description = 'Preview'

    list_display = ('title', 'thumbnail', 'category', 'is_featured', 'uploaded_at')  # ✅ added category
    list_editable = ('category', 'is_featured')  # ✅ editable in list
    ordering = ('-uploaded_at',)
    date_hierarchy = 'uploaded_at'
    list_filter = ('category', 'is_featured')  # ✅ filter by category too
    search_fields = ('title',)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'added_at')
    list_filter = ('category',)
    ordering = ('-added_at',)
    date_hierarchy = 'added_at'
    search_fields = ('name',)
    list_editable = ('category',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'item', 'date', 'phone', 'created_at', 'notified')
    list_editable = ('notified',)
    readonly_fields = ('created_at', 'image_preview')
    list_filter = ('date', 'created_at', 'notified')
    search_fields = ('name', 'email', 'item', 'phone')
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('name', 'email', 'phone', 'item', 'date', 'notes', 'reference_image', 'image_preview')
        }),
        ('Status', {
            'fields': ('notified', 'created_at'),
        }),
    )

    def image_preview(self, obj):
        if obj.reference_image:
            return format_html('<img src="{}" style="max-height: 200px;" />', obj.reference_image.url)
        return "(No image)"
    image_preview.short_description = "Uploaded Image Preview"
