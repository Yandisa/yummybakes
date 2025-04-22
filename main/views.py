from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from urllib.parse import quote
from .models import Testimonial, GalleryImage, MenuItem, Order
from .forms import TestimonialForm
import random


def home(request):
    """Display home page with a random featured testimonial"""
    testimonials = Testimonial.objects.filter(is_approved=True)
    featured = random.choice(testimonials) if testimonials else None
    return render(request, 'main/home.html', {
        'featured_testimonial': featured
    })


def about(request):
    """Display the about page"""
    return render(request, 'main/about.html')


def menu(request):
    """Display menu items sorted by name"""
    items = MenuItem.objects.order_by('name')
    return render(request, 'main/menu.html', {'items': items})


def gallery(request):
    """Display gallery images sorted by upload date"""
    images = GalleryImage.objects.order_by('-uploaded_at')
    return render(request, 'main/gallery.html', {'images': images})


def order(request):
    """Process and submit an order"""
    if request.method == 'POST':
        try:
            required_fields = ['name', 'phone', 'item', 'date']
            if not all(field in request.POST for field in required_fields):
                raise ValueError("Missing required fields")

            order = Order.objects.create(
                name=request.POST['name'],
                phone=request.POST['phone'],
                item=request.POST['item'],
                date=request.POST['date'],
                notes=request.POST.get('notes', ''),
                reference_image=request.FILES.get('reference_image')
            )

            message = (
                f"New Order:\n"
                f"Name: {order.name}\n"
                f"Phone: {order.phone}\n"
                f"Item: {order.item}\n"
                f"Date: {order.date}\n"
                f"Notes: {order.notes or 'None'}"
            )
            whatsapp_url = f"https://wa.me/27849523821?text={quote(message)}"

            return render(request, 'main/order.html', {
                'whatsapp_url': whatsapp_url,
                'submitted': True
            })

        except Exception as e:
            messages.error(request, f"Error processing order: {str(e)}")
            return redirect('order')

    return render(request, 'main/order.html')


def testimonials(request):
    """Submit and display customer testimonials"""
    testimonials = Testimonial.objects.filter(
        is_approved=True
    ).order_by('-created_at')

    if request.method == 'POST':
        form = TestimonialForm(request.POST)
        if form.is_valid():
            testimonial = form.save(commit=False)
            testimonial.is_approved = False
            testimonial.save()
            messages.success(
                request,
                "Thank you! Your testimonial is pending approval."
            )
            return redirect('testimonials')
    else:
        form = TestimonialForm()

    return render(request, 'main/testimonials.html', {
        'testimonials': testimonials,
        'form': form
    })


def thank_you(request):
    """Display thank-you page with order confirmation"""
    name = request.GET.get('name', '')
    item = request.GET.get('item', '')
    date = request.GET.get('date', '')
    notes = request.GET.get('notes', '')

    message = (
        f"Order Confirmation:\n"
        f"Name: {name}\n"
        f"Item: {item}\n"
        f"Date: {date}\n"
        f"Notes: {notes or 'None'}"
    )
    whatsapp_url = f"https://wa.me/27849523821?text={quote(message)}"

    return render(request, 'main/thank_you.html', {
        'whatsapp_url': whatsapp_url,
        'name': name
    })


def contact(request):
    """Display the contact page"""
    return render(request, 'main/contact.html')


def faq(request):
    """Display frequently asked questions"""
    return render(request, 'main/faq.html')


def handler404(request, exception):
    """Custom 404 error page."""
    return render(request, 'main/404.html', status=404)


def handler500(request):
    """Custom 500 error page."""
    return render(request, 'main/500.html', status=500)
