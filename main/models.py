import os
import io
from django.db import models
from django.core.files.base import ContentFile
from PIL import Image


def compress_image(image_field, max_size=(1200, 1200), quality=82):
    """Resize and compress an image field in place, converting to JPEG."""
    img = Image.open(image_field)

    # Convert RGBA/P to RGB so JPEG save works
    if img.mode in ('RGBA', 'P', 'LA'):
        img = img.convert('RGB')

    # Resize keeping aspect ratio
    img.thumbnail(max_size, Image.LANCZOS)

    output = io.BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)

    # Strip extension and force .jpg
    base = os.path.splitext(os.path.basename(image_field.name))[0]
    return ContentFile(output.read(), name=f"{base}.jpg")


class Testimonial(models.Model):
    """Model to store customer testimonials"""
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimonials"

    def __str__(self):
        return f"{self.name} ({self.location})"


class GalleryImage(models.Model):
    """Image used as inspiration or sample design"""
    CATEGORY_CHOICES = [
        ('wedding', 'Wedding Cakes'),
        ('birthday', 'Birthday Cakes'),
        ('kids', 'Kids Cakes'),
        ('custom', 'Custom Designs'),
        ('muffins', 'Muffins'),
        ('cupcakes', 'Cupcakes'),
        ('scones', 'Scones'),
        ('party_packs', 'Party Packs'),
        ('balloons', 'Balloon Garlands'),
        ('specials', 'Specials'),
    ]

    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='gallery/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default=False)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='custom')

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Gallery Image"
        verbose_name_plural = "Gallery Images"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.image and hasattr(self.image, 'file'):
            self.image = compress_image(self.image, max_size=(1200, 1200), quality=82)
        super().save(*args, **kwargs)


class MenuItem(models.Model):
    CATEGORY_CHOICES = GalleryImage.CATEGORY_CHOICES

    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='menu/')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='custom')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.image and hasattr(self.image, 'file'):
            self.image = compress_image(self.image, max_size=(1200, 1200), quality=82)
        super().save(*args, **kwargs)


class Order(models.Model):
    """Customer order submission"""
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    item = models.CharField(max_length=100)
    date = models.DateField()
    notes = models.TextField(blank=True)
    reference_image = models.ImageField(upload_to='orders/', blank=True, null=True)
    gallery_design = models.ForeignKey(GalleryImage, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"{self.name} - {self.item} ({self.date})"

    def save(self, *args, **kwargs):
        if self.reference_image and hasattr(self.reference_image, 'file'):
            self.reference_image = compress_image(self.reference_image, max_size=(1200, 1200), quality=82)
        super().save(*args, **kwargs)
