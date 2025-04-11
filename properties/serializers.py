from rest_framework import serializers
from .models import Property, PropertyImage, PropertyReview, Amenity

class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ['id', 'name', 'icon']

class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'is_primary', 'created_at']

class PropertyReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = PropertyReview
        fields = ['id', 'rating', 'comment', 'created_at', 'user_name']

class PropertySerializer(serializers.ModelSerializer):
    images = PropertyImageSerializer(many=True, read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)
    reviews = PropertyReviewSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = Property
        fields = [
            'id', 'name', 'description', 'location', 'address',
            'price_per_night', 'status', 'rating', 'average_rating',
            'images', 'amenities', 'reviews', 'owner_name',
            'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        amenities_data = self.context['request'].data.get('amenities', [])
        images_data = self.context['request'].data.getlist('images', [])
        
        property = Property.objects.create(**validated_data)
        
        # Add amenities
        if amenities_data:
            property.amenities.set(amenities_data)
        
        # Add images
        for image_data in images_data:
            PropertyImage.objects.create(property=property, image=image_data)
        
        return property

    def update(self, instance, validated_data):
        amenities_data = self.context['request'].data.get('amenities', [])
        images_data = self.context['request'].data.getlist('images', [])
        
        # Update property fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update amenities if provided
        if amenities_data:
            instance.amenities.set(amenities_data)
        
        # Add new images if provided
        for image_data in images_data:
            PropertyImage.objects.create(property=instance, image=image_data)
        
        return instance