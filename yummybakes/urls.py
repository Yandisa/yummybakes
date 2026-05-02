from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from main import views
from django.views.generic import TemplateView

urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),

    # Core Pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('menu/', views.menu, name='menu'),
    path('menu/<str:category>/', views.menu_category, name='menu_category'),  # ✅ NEW: category-based view

    # Gallery & Reviews
    path('gallery/', views.gallery, name='gallery'),
    path('testimonials/', views.testimonials, name='testimonials'),

    # Order Flow
    path('order/', views.order, name='order'),
    path('thank-you/<int:order_id>/', views.thank_you, name='thank_you'),

    # Support Pages
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),

    # User Authentication (security enhanced)
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(
        next_page='home',
        template_name='registration/logged_out.html'
    ), name='logout'),

    # Google Site Verification
    path('google531f105f9bd65559.html', TemplateView.as_view(template_name="google531f105f9bd65559.html")),
]

# Custom error handlers (these should be at module level, not inside urlpatterns)
handler404 = 'main.views.handler404'
handler500 = 'main.views.handler500'
handler403 = 'main.views.permission_denied'  # You were missing this before

# Static & Media files configuration
if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
