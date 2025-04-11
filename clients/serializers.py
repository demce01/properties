from rest_framework import serializers
from .models import ClientProfile

class ClientProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = ClientProfile
        fields = ['id', 'username', 'email', 'phone_number', 'address', 
                 'preferred_contact', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']