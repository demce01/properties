from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'api/payments', views.PaymentViewSet)

urlpatterns = [
    path('', views.payments_list, name='payments_list'),
    path('create/', views.payment_create, name='payment_create'),
    path('<int:payment_id>/complete/', views.payment_complete, name='payment_complete'),
    path('<int:payment_id>/', views.payment_details, name='payment_details'),
] + router.urls