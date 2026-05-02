from django.db import models


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
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='custom')  # ✅ New field

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Gallery Image"
        verbose_name_plural = "Gallery Images"

    def __str__(self):
        return self.title


class MenuItem(models.Model):
    CATEGORY_CHOICES = GalleryImage.CATEGORY_CHOICES  # Reuse same choices for consistency

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
