from django.db import models


class Testimonial(models.Model):
    """Model to store customer testimonials"""
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.location})"


class GalleryImage(models.Model):
    """Image gallery with upload date"""
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='gallery/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class MenuItem(models.Model):
    """Item listed on the menu with price and image"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='menu/')
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    """Customer order submission"""
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    item = models.CharField(max_length=100)
    date = models.DateField()
    notes = models.TextField(blank=True)
    reference_image = models.ImageField(
        upload_to='orders/', blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.item} ({self.date})"
