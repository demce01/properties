from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class CustomUser(AbstractUser):
    is_client = models.BooleanField(default=False)
    is_owner = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class Amenity(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, help_text="Font Awesome icon class name")
    
    class Meta:
        verbose_name_plural = "amenities"
    
    def __str__(self):
        return self.name

class Property(models.Model):
    STATUS_CHOICES = (
        ('Available', 'Available'),
        ('Occupied', 'Occupied'),
        ('Maintenance', 'Maintenance'),
    )
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='properties')
    name = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200, default='Not specified')
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available')
    amenities = models.ManyToManyField(Amenity, related_name='properties')
    rating = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        default=0
    )
    address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "properties"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0

class PropertyImage(models.Model):
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='property_images/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', '-created_at']
    
    def __str__(self):
        return f"Image for {self.property.name}"

class PropertyReview(models.Model):
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='property_reviews'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['property', 'user']
    
    def __str__(self):
        return f"Review for {self.property.name} by {self.user.username}"

# Add test data for properties
def add_test_properties():
    owner = CustomUser.objects.first()  # Use the first user as the owner
    Property.objects.create(
        owner=owner,
        name="Cozy Apartment",
        description="A cozy apartment in the city center.",
        price_per_night=100.00,
        address="123 Main Street, Cityville",
    )
    Property.objects.create(
        owner=owner,
        name="Beach House",
        description="A beautiful beach house with ocean views.",
        price_per_night=200.00,
        address="456 Ocean Drive, Beachtown",
    )
