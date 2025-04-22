from django.contrib import admin
from .models import Testimonial, GalleryImage, MenuItem, Order


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    # Display these fields in the admin list view
    list_display = ('name', 'location', 'is_approved', 'created_at')
    # Add filters in the right sidebar
    list_filter = ('is_approved',)
    # Add a search bar for specified fields
    search_fields = ('name', 'location', 'message')
    # Sort newest first
    ordering = ('-created_at',)


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_at')
    ordering = ('-uploaded_at',)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'added_at')
    ordering = ('-added_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'item', 'date', 'phone', 'created_at', 'notified'
    )
    readonly_fields = ('created_at',)
    list_filter = ('date', 'created_at', 'notified')
    search_fields = ('name', 'item', 'phone')
