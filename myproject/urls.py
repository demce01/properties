"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from properties.views import (
    PropertyViewSet, property_list, property_create, 
    dashboard, dashboard_stats
)
from bookings.views import (
    BookingViewSet, BookingReviewViewSet,
    bookings_list, booking_create, booking_calendar, booking_cancel,
    create_review, property_reviews
)
from payments.views import PaymentViewSet, payments_list
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename='property')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'reviews', BookingReviewViewSet, basename='review')
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/dashboard/stats/', dashboard_stats, name='dashboard_stats'),  # Add this line
    path('api/login/', auth_views.LoginView.as_view(), name='login'),
    path('api/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', dashboard, name='dashboard'),
    path('properties/', property_list, name='properties_list'),
    path('properties/create/', property_create, name='property_create'),
    path('bookings/', bookings_list, name='bookings_list'),
    path('bookings/create/', booking_create, name='booking_create'),
    path('bookings/calendar/', booking_calendar, name='booking_calendar'),
    path('bookings/<int:booking_id>/cancel/', booking_cancel, name='booking_cancel'),
    path('bookings/<int:booking_id>/review/', create_review, name='create_review'),
    path('properties/<int:property_id>/reviews/', property_reviews, name='property_reviews'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='dashboard'), name='logout'),
    path('payments/', include('payments.urls')),
    path('clients/', include('clients.urls')),  # Add this line
    
    # Password reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
]

# Serve static and media files in development
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
