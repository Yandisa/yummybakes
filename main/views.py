import os
import logging
from urllib.parse import quote
from collections import defaultdict, OrderedDict

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.core.mail import EmailMessage, EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string

from .models import Testimonial, GalleryImage, MenuItem, Order
from .forms import TestimonialForm, OrderForm

logger = logging.getLogger(__name__)


def home(request):
    featured_cakes = GalleryImage.objects.filter(is_featured=True).order_by('-uploaded_at')[:6]
    testimonials = Testimonial.objects.filter(is_approved=True).order_by('-created_at')[:3]

    return render(request, 'main/home.html', {
        'featured_cakes': featured_cakes,
        'testimonials': testimonials,
    })


def about(request):
    return render(request, 'main/about.html')


def menu(request):
    """Show all categories that have at least one MenuItem"""
    # Get all unique categories that have menu items, with a sample image from each
    items = MenuItem.objects.all().order_by('category', '-added_at')
 
    # Build category cards dynamically — one card per category that has items
    seen = set()
    category_cards = []
    for item in items:
        if item.category not in seen:
            seen.add(item.category)
            category_cards.append({
                'key': item.category,
                'label': item.get_category_display(),
                'image_url': item.image.url,
                'item_count': MenuItem.objects.filter(category=item.category).count(),
            })
 
    return render(request, 'main/menu.html', {
        'category_cards': category_cards,
    })
 
 
def menu_category(request, category):
    """Show all menu items in a specific category"""
    # Validate the category against MenuItem's choices
    valid_categories = dict(MenuItem.CATEGORY_CHOICES)
    if category not in valid_categories:
        from django.http import Http404
        raise Http404("Category not found.")
 
    items = MenuItem.objects.filter(category=category).order_by('-added_at')
 
    return render(request, 'main/menu_category.html', {
        'items': items,
        'category_key': category,
        'category_label': valid_categories[category],
    })

def gallery(request):
    images = GalleryImage.objects.all().order_by('-uploaded_at')
    return render(request, 'main/gallery.html', {'images': images})


def faq(request):
    faqs = [
        (2, "How do I place a custom order?", "You can use our <a href='/order/'>Order</a> page or contact us directly via WhatsApp with your custom request."),
        (3, "What payment methods do you accept?", "We currently accept EFT (Electronic Funds Transfer) and cash. Card payments will be available soon — stay tuned!"),
        (4, "How far in advance should I place my order?", "For custom cakes, 3–5 days’ notice is ideal. For cupcakes or cookies, 1–2 days is usually enough."),
        (5, "How do I confirm my order?", "Once we receive your order details, we’ll send a confirmation via WhatsApp or email. Orders are only confirmed after at least 50% payment (for EFT payments)."),
        (6, "What flavors do you offer?", "We bake classics like vanilla, chocolate, red velvet, lemon, caramel, and carrot. Custom flavors can be arranged too!"),
        (7, "Can I send a cake as a gift to someone else?", "Definitely! Just provide their name, address, and phone number, and we’ll handle the sweet surprise."),
        (8, "What happens if I need to cancel my order?", "You can cancel up to 24 hours before pickup or delivery. Custom orders may not be refundable once baking has started."),
        (9, "Can I pick up my order instead of delivery?", "Absolutely! Pickup is available in Tsomo. We’ll confirm the time and address once your order is placed."),
        (10, "Do you make custom cakes or designs?", "Yes! We love bringing your ideas to life. Just share your theme or inspiration when placing your order."),
    ]
    return render(request, 'main/faq.html', {'faqs': faqs})


@require_http_methods(["GET", "POST"])


def order(request):
    initial_data = {}
    if 'item' in request.GET:
        initial_data['item'] = request.GET['item']

    form = OrderForm(request.POST or None, request.FILES or None, initial=initial_data)

    if request.method == 'POST':
        if form.is_valid():
            order = form.save()
            logger.info(f"[ORDER] New order placed by {order.name}")

            # Get item image from GalleryImage or similar
            item_image = GalleryImage.objects.filter(title__iexact=order.item).first()
            image_url = request.build_absolute_uri(item_image.image.url) if item_image else None

            # Send HTML admin email
            try:
                subject = f"New Order from {order.name}"
                html_body = render_to_string('emails/admin_order_notification.html', {
                    'order': order,
                    'image_url': image_url
                })

                admin_email = EmailMultiAlternatives(
                    subject=subject,
                    body="New order received (see HTML version)",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=['xolagaju8@gmail.com'],
                )
                admin_email.attach_alternative(html_body, "text/html")

                if order.reference_image:
                    admin_email.attach_file(order.reference_image.path)

                admin_email.send(fail_silently=False)
            except Exception as e:
                logger.warning(f"[EMAIL_ERROR] Failed to send admin email: {e}")
                messages.warning(request, "⚠️ Order saved, but admin email failed.")

            # Send customer confirmation
            if order.email:
                try:
                    html_content = render_to_string('emails/order_confirmation.html', {'order': order})
                    customer_email = EmailMessage(
                        subject="Your Yummy Bakes Order Confirmation",
                        body=html_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[order.email],
                    )
                    customer_email.content_subtype = "html"
                    customer_email.send(fail_silently=False)
                except Exception as e:
                    logger.warning(f"[EMAIL_ERROR] Failed to send customer confirmation email: {e}")
                    messages.warning(request, "⚠️ Confirmation email to customer failed.")

            return redirect('thank_you', order_id=order.id)
        else:
            messages.error(request, "⚠️ Please correct the errors below.")

    return render(request, 'main/order.html', {'form': form})

def thank_you(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    message = (
        "Order Confirmation:\n"
        f"Name: {order.name}\n"
        f"Phone: {order.phone}\n"
        f"Item: {order.item}\n"
        f"Date: {order.date.strftime('%Y-%m-%d')}\n"
        f"Notes: {order.notes or 'None'}"
    )

    whatsapp_url = f"https://wa.me/27849523821?text={quote(message)}"

    return render(request, 'main/thank_you.html', {
        'order': order,
        'whatsapp_url': whatsapp_url
    })


def testimonials(request):
    approved_testimonials = Testimonial.objects.filter(is_approved=True).order_by('-created_at')[:10]
    form = TestimonialForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            testimonial = form.save(commit=False)
            testimonial.ip_address = request.META.get('REMOTE_ADDR', 'unknown')
            testimonial.save()
            logger.info(f"[TESTIMONIAL] New submission from {testimonial.name}")
            messages.success(request, "Thank you! Your testimonial is pending approval.")
            return redirect('testimonials')
        else:
            messages.error(request, "Please correct the errors below.")
    return render(request, 'main/testimonials.html', {'testimonials': approved_testimonials, 'form': form})


def serve_protected_media(request, path):
    safe_path = os.path.normpath(path).lstrip('/')
    full_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, safe_path))
    if not full_path.startswith(os.path.abspath(settings.MEDIA_ROOT)):
        logger.warning(f"[SECURITY] Directory traversal blocked: {safe_path}")
        raise PermissionDenied("Invalid media path.")
    if not os.path.exists(full_path):
        logger.info(f"[404] Media not found: {safe_path}")
        raise Http404("File not found.")
    return FileResponse(open(full_path, 'rb'), content_type='application/octet-stream')


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        full_message = f"Message from {name} ({email}):\n\n{message}"

        send_mail(
            subject=f"New Contact Form Message from {name}",
            message=full_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['xolagaju8@gmail.com'],  # or your preferred email
            fail_silently=False,
        )

        messages.success(request, 'Thanks for contacting us! We’ll get back to you shortly.')
        return redirect('contact')  # or any page you prefer

    return render(request, 'main/contact.html')



def handler404(request, exception):
    return render(request, 'main/404.html', status=404)

def handler500(request):
    return render(request, 'main/500.html', status=500)

def permission_denied(request, exception=None):
    return render(request, 'main/403.html', status=403)
