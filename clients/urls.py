from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'api/clients', views.ClientProfileViewSet)

urlpatterns = [
    path('', views.clients_list, name='clients_list'),
    path('<int:client_id>/', views.client_profile, name='client_profile'),
    path('create/', views.client_create, name='client_create'),  # Add this line
] + router.urls