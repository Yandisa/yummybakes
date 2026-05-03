import os
import io
import logging
import mimetypes
import urllib.request
from urllib.parse import quote
from collections import defaultdict, OrderedDict

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
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
    """Show all categories that have at least one GalleryImage — one face card per category"""
    images = GalleryImage.objects.all().order_by('category', '-uploaded_at')

    seen = set()
    category_cards = []
    for img in images:
        if img.category not in seen:
            seen.add(img.category)
            # Get lowest price from MenuItem for this category
            from django.db.models import Min
            price_data = MenuItem.objects.filter(category=img.category).aggregate(min_price=Min('price'))
            min_price = price_data['min_price']
            category_cards.append({
                'key': img.category,
                'label': img.get_category_display(),
                'image_url': img.image.url,
                'item_count': GalleryImage.objects.filter(category=img.category).count(),
                'from_price': min_price,
            })

    return render(request, 'main/menu.html', {
        'category_cards': category_cards,
    })


def menu_category(request, category):
    """Show all gallery images in a specific category"""
    valid_categories = dict(GalleryImage.CATEGORY_CHOICES)
    if category not in valid_categories:
        raise Http404("Category not found.")

    gallery_images = GalleryImage.objects.filter(category=category).order_by('-uploaded_at')

    return render(request, 'main/menu_category.html', {
        'gallery_images': gallery_images,
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
        (4, "How far in advance should I place my order?", "For custom cakes, 3–5 days' notice is ideal. For cupcakes or cookies, 1–2 days is usually enough."),
        (5, "How do I confirm my order?", "Once we receive your order details, we'll send a confirmation via WhatsApp or email. Orders are only confirmed after at least 50% payment (for EFT payments)."),
        (6, "What flavors do you offer?", "We bake classics like vanilla, chocolate, red velvet, lemon, caramel, and carrot. Custom flavors can be arranged too!"),
        (7, "Can I send a cake as a gift to someone else?", "Definitely! Just provide their name, address, and phone number, and we'll handle the sweet surprise."),
        (8, "What happens if I need to cancel my order?", "You can cancel up to 24 hours before pickup or delivery. Custom orders may not be refundable once baking has started."),
        (9, "Can I pick up my order instead of delivery?", "Absolutely! Pickup is available in Tsomo. We'll confirm the time and address once your order is placed."),
        (10, "Do you make custom cakes or designs?", "Yes! We love bringing your ideas to life. Just share your theme or inspiration when placing your order."),
    ]
    return render(request, 'main/faq.html', {'faqs': faqs})


@require_http_methods(["GET", "POST"])
def order(request):
    initial_data = {}
    selected_image_url = None

    if request.method == 'GET':
        if 'item' in request.GET:
            initial_data['item'] = request.GET['item']
        if 'img_url' in request.GET:
            selected_image_url = request.GET['img_url']

    if request.method == 'POST':
        selected_image_url = request.POST.get('selected_image_url')

    form = OrderForm(request.POST or None, request.FILES or None, initial=initial_data)

    if request.method == 'POST':
        if form.is_valid():
            order_obj = form.save(commit=False)

            # Auto-attach gallery image if no reference image uploaded
            if not order_obj.reference_image and selected_image_url:
                try:
                    # Build absolute path from media URL
                    media_url = settings.MEDIA_URL
                    if selected_image_url.startswith(media_url):
                        relative_path = selected_image_url[len(media_url):]
                        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                        if os.path.exists(full_path):
                            with open(full_path, 'rb') as f:
                                filename = os.path.basename(full_path)
                                order_obj.reference_image.save(filename, ContentFile(f.read()), save=False)
                except Exception as e:
                    logger.warning(f"[ORDER] Could not attach gallery image: {e}")

            order_obj.save()
            logger.info(f"[ORDER] New order placed by {order_obj.name}")

            image_url = request.build_absolute_uri(order_obj.reference_image.url) if order_obj.reference_image else None

            # Send HTML admin email
            try:
                subject = f"New Order from {order_obj.name}"
                html_body = render_to_string('emails/admin_order_notification.html', {
                    'order': order_obj,
                    'image_url': image_url
                })

                admin_email = EmailMultiAlternatives(
                    subject=subject,
                    body="New order received (see HTML version)",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=['xolagaju8@gmail.com'],
                )
                admin_email.attach_alternative(html_body, "text/html")

                if order_obj.reference_image:
                    admin_email.attach_file(order_obj.reference_image.path)

                admin_email.send(fail_silently=False)
            except Exception as e:
                logger.warning(f"[EMAIL_ERROR] Failed to send admin email: {e}")
                messages.warning(request, "⚠️ Order saved, but admin email failed.")

            # Send customer confirmation
            if order_obj.email:
                try:
                    html_content = render_to_string('emails/order_confirmation.html', {'order': order_obj})
                    customer_email = EmailMessage(
                        subject="Your Yummy Bakes Order Confirmation",
                        body=html_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[order_obj.email],
                    )
                    customer_email.content_subtype = "html"
                    customer_email.send(fail_silently=False)
                except Exception as e:
                    logger.warning(f"[EMAIL_ERROR] Failed to send customer confirmation: {e}")
                    messages.warning(request, "⚠️ Confirmation email to customer failed.")

            return redirect('thank_you', order_id=order_obj.id)
        else:
            messages.error(request, "⚠️ Please correct the errors below.")

    return render(request, 'main/order.html', {
        'form': form,
        'selected_image_url': selected_image_url,
    })


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
    mime_type, _ = mimetypes.guess_type(full_path)
    mime_type = mime_type or 'application/octet-stream'
    response = FileResponse(open(full_path, 'rb'), content_type=mime_type)
    max_age = getattr(settings, 'MEDIA_CACHE_MAX_AGE', 60 * 60 * 24 * 30)
    response['Cache-Control'] = f'public, max-age={max_age}'
    return response


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
            recipient_list=['xolagaju8@gmail.com'],
            fail_silently=False,
        )

        messages.success(request, "Thanks for contacting us! We'll get back to you shortly.")
        return redirect('contact')

    return render(request, 'main/contact.html')


def handler404(request, exception):
    return render(request, 'main/404.html', status=404)

def handler500(request):
    return render(request, 'main/500.html', status=500)

def permission_denied(request, exception=None):
    return render(request, 'main/403.html', status=403)
