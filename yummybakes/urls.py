from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from main import views

urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),

    # Core Pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('menu/', views.menu, name='menu'),

    # Gallery & Reviews
    path('gallery/', views.gallery, name='gallery'),
    path('testimonials/', views.testimonials, name='testimonials'),

    # Order Flow
    path('order/', views.order, name='order'),
    path('thank-you/', views.thank_you, name='thank_you'),

    # Support Pages
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),

    # User Authentication
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(
        next_page='home'
    ), name='logout'),
]

# Custom error handlers
handler404 = 'main.views.handler404'
handler500 = 'main.views.handler500'

# Static & Media files in development
if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
