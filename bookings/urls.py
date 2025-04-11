from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'api/bookings', views.BookingViewSet)
router.register(r'api/reviews', views.BookingReviewViewSet)

urlpatterns = [
    path('', views.bookings_list, name='bookings_list'),
    path('create/', views.booking_create, name='booking_create'),
    path('calendar/', views.booking_calendar, name='booking_calendar'),
    path('<int:booking_id>/cancel/', views.booking_cancel, name='booking_cancel'),
    path('<int:booking_id>/review/', views.create_review, name='create_review'),
    path('property/<int:property_id>/reviews/', views.property_reviews, name='property_reviews'),
] + router.urls