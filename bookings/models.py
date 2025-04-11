from django.db import models
from properties.models import Property
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Booking(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking for {self.property.name} by {self.client.username}"

class BookingReview(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return f"Review for booking {self.booking.id}"

    def save(self, *args, **kwargs):
        # Update property rating when review is saved
        super().save(*args, **kwargs)
        property = self.booking.property
        avg_rating = BookingReview.objects.filter(
            booking__property=property,
            is_public=True
        ).aggregate(models.Avg('rating'))['rating__avg']
        if avg_rating:
            property.rating = avg_rating
            property.save()
