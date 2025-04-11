from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from .models import Booking, BookingReview
from properties.models import Property
from datetime import datetime, timedelta
from rest_framework import viewsets, permissions
from .serializers import BookingSerializer, BookingReviewSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

class BookingReviewViewSet(viewsets.ModelViewSet):
    queryset = BookingReview.objects.all()
    serializer_class = BookingReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Ensure the user can only review their own bookings
        booking = get_object_or_404(
            Booking, 
            id=self.request.data.get('booking'),
            client=self.request.user
        )
        serializer.save(booking=booking)

@login_required
def bookings_list(request):
    # Get all bookings with related properties and clients
    bookings = Booking.objects.select_related('property', 'client').all()
    
    # Get recent bookings for the sidebar
    recent_bookings = bookings.order_by('-created_at')[:5]
    
    # Get all properties for the booking form
    properties = Property.objects.all()
    
    # Get all clients for the booking form
    User = get_user_model()
    clients = User.objects.filter(is_client=True)
    
    context = {
        'bookings': bookings,
        'recent_bookings': recent_bookings,
        'properties': properties,
        'clients': clients,
        'today': datetime.now().date(),  # Add today's date for template logic
    }
    return render(request, 'bookings.html', context)

@login_required
def booking_create(request):
    if request.method == 'POST':
        try:
            property_id = request.POST.get('property')
            client_id = request.POST.get('client')
            start_date = datetime.strptime(request.POST.get('start_date'), '%Y-%m-%d')
            end_date = datetime.strptime(request.POST.get('end_date'), '%Y-%m-%d')
            
            # Calculate total price based on property price and number of nights
            property = Property.objects.get(id=property_id)
            nights = (end_date - start_date).days
            total_price = property.price_per_night * nights
            
            booking = Booking.objects.create(
                property_id=property_id,
                client_id=client_id,
                start_date=start_date,
                end_date=end_date,
                total_price=total_price
            )
            messages.success(request, 'Booking created successfully!')
            return redirect('bookings_list')
        except Exception as e:
            messages.error(request, f'Error creating booking: {str(e)}')
            return redirect('bookings_list')

@login_required
def booking_calendar(request):
    """Return bookings in a format suitable for FullCalendar."""
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    bookings = Booking.objects.filter(
        start_date__gte=start,
        end_date__lte=end
    ).select_related('property', 'client')
    
    events = []
    for booking in bookings:
        events.append({
            'id': booking.id,
            'title': f'{booking.property.name} - {booking.client.username}',
            'start': booking.start_date.isoformat(),
            'end': booking.end_date.isoformat(),
            'className': 'bg-primary'
        })
    
    return JsonResponse(events, safe=False)

@login_required
def booking_cancel(request, booking_id):
    """Cancel a booking."""
    try:
        booking = Booking.objects.get(id=booking_id)
        booking.status = 'Cancelled'
        booking.save()
        messages.success(request, 'Booking cancelled successfully!')
        return JsonResponse({'status': 'success'})
    except Booking.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def create_review(request, booking_id):
    if request.method == 'POST':
        try:
            booking = get_object_or_404(Booking, id=booking_id, client=request.user)
            
            # Check if review already exists
            if hasattr(booking, 'review'):
                messages.error(request, 'You have already reviewed this booking')
                return redirect('bookings_list')
            
            review = BookingReview.objects.create(
                booking=booking,
                rating=request.POST.get('rating'),
                comment=request.POST.get('comment'),
                is_public=True
            )
            messages.success(request, 'Review submitted successfully!')
            return redirect('bookings_list')
        except Exception as e:
            messages.error(request, f'Error submitting review: {str(e)}')
            return redirect('bookings_list')

@login_required
def property_reviews(request, property_id):
    """View all reviews for a specific property."""
    property = get_object_or_404(Property, id=property_id)
    reviews = BookingReview.objects.filter(
        booking__property=property,
        is_public=True
    ).select_related('booking', 'booking__client')
    
    context = {
        'property': property,
        'reviews': reviews,
    }
    return render(request, 'property_reviews.html', context)
