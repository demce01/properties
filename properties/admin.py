from django.contrib import admin
from .models import Amenity, Property, PropertyImage, PropertyReview, CustomUser

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'price_per_night', 'status', 'rating')
    list_filter = ('status', 'amenities')
    search_fields = ('name', 'location', 'description')

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')

@admin.register(PropertyReview)
class PropertyReviewAdmin(admin.ModelAdmin):
    list_display = ('property', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_client', 'is_owner', 'is_admin')
    list_filter = ('is_client', 'is_owner', 'is_admin')
    search_fields = ('username', 'email')

