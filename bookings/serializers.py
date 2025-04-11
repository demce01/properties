from rest_framework import serializers
from .models import Booking, BookingReview

class BookingReviewSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='booking.client.username', read_only=True)
    property_name = serializers.CharField(source='booking.property.name', read_only=True)
    
    class Meta:
        model = BookingReview
        fields = ['id', 'booking', 'rating', 'comment', 'created_at', 
                 'is_public', 'client_name', 'property_name']
        read_only_fields = ['created_at']

class BookingSerializer(serializers.ModelSerializer):
    review = BookingReviewSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'