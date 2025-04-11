from django.contrib import admin
from .models import ClientProfile

@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'preferred_contact', 'created_at')
    list_filter = ('preferred_contact', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number')
