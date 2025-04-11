from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, Sum
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Property, PropertyImage, Amenity, CustomUser
from .serializers import PropertySerializer
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta

class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.prefetch_related('images', 'amenities').all()
    serializer_class = PropertySerializer
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse(
                {'status': 'error', 'message': str(e)}, 
                status=500
            )

@login_required
def property_list(request):
    properties = Property.objects.prefetch_related('images', 'amenities').all()
    
    # Calculate statistics
    stats = {
        'total_properties': Property.objects.count(),
        'available_properties': Property.objects.filter(status='Available').count(),
        'occupied_properties': Property.objects.filter(status='Occupied').count(),
        'average_price': Property.objects.aggregate(
            avg_price=Avg('price_per_night')
        )['avg_price'] or 0
    }
    
    # Get all amenities for the add property form
    all_amenities = Amenity.objects.all()
    
    context = {
        'properties': properties,
        'stats': stats,
        'all_amenities': all_amenities,
    }
    return render(request, 'properties.html', context)

@login_required
@require_http_methods(['POST'])
def property_create(request):
    try:
        property = Property.objects.create(
            name=request.POST['name'],
            location=request.POST['location'],
            description=request.POST['description'],
            price_per_night=request.POST['price_per_night'],
            status='Available'
        )
        
        # Handle amenities
        if 'amenities' in request.POST:
            amenities = request.POST.getlist('amenities')
            property.amenities.set(amenities)
        
        # Handle images
        if 'images' in request.FILES:
            for image in request.FILES.getlist('images'):
                PropertyImage.objects.create(
                    property=property,
                    image=image
                )
        
        messages.success(request, 'Property created successfully!')
        return redirect('property_list')
    except Exception as e:
        messages.error(request, f'Error creating property: {str(e)}')
        return redirect('property_list')

@login_required
def property_edit(request, property_id):
    property = get_object_or_404(Property, id=property_id)
    
    if request.method == 'POST':
        try:
            property.name = request.POST['name']
            property.location = request.POST['location']
            property.description = request.POST['description']
            property.price_per_night = request.POST['price_per_night']
            property.save()
            
            # Update amenities
            if 'amenities' in request.POST:
                property.amenities.set(request.POST.getlist('amenities'))
            
            # Add new images
            if 'images' in request.FILES:
                for image in request.FILES.getlist('images'):
                    PropertyImage.objects.create(
                        property=property,
                        image=image
                    )
            
            messages.success(request, 'Property updated successfully!')
            return redirect('property_list')
        except Exception as e:
            messages.error(request, f'Error updating property: {str(e)}')
    
    context = {
        'property': property,
        'all_amenities': Amenity.objects.all(),
    }
    return render(request, 'property_edit.html', context)

@login_required
@require_http_methods(['DELETE'])
def property_image_delete(request, image_id):
    try:
        image = get_object_or_404(PropertyImage, id=image_id)
        image.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'message': str(e)}, 
            status=500
        )

@login_required
def dashboard(request):
    # Get dashboard statistics
    today = datetime.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    stats = {
        'total_properties': Property.objects.count(),
        'active_bookings': Property.objects.filter(
            bookings__start_date__lte=today,
            bookings__end_date__gte=today
        ).count(),
        'monthly_revenue': Property.objects.filter(
            bookings__start_date__gte=thirty_days_ago
        ).aggregate(
            total=Sum('bookings__total_price')
        )['total'] or 0,
        'total_clients': Property.objects.values('bookings__client').distinct().count()
    }
    
    # Get data needed for modals
    properties = Property.objects.filter(status='Available')
    clients = CustomUser.objects.filter(is_client=True)
    
    # Get recent activities
    recent_activities = []  # You'll need to implement an Activity model to track this
    
    # Get upcoming bookings
    upcoming_bookings = Property.objects.filter(
        bookings__start_date__gte=today
    ).order_by('bookings__start_date')[:5]
    
    context = {
        'stats': stats,
        'recent_activities': recent_activities,
        'upcoming_bookings': upcoming_bookings,
        'properties': properties,  # Add this for the booking modal
        'clients': clients,  # Add this for the booking modal
    }
    return render(request, 'home.html', context)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    today = datetime.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    stats = {
        'total_properties': Property.objects.count(),
        'active_bookings': Property.objects.filter(
            bookings__start_date__lte=today,
            bookings__end_date__gte=today
        ).count(),
        'monthly_revenue': Property.objects.filter(
            bookings__start_date__gte=thirty_days_ago
        ).aggregate(
            total=Sum('bookings__total_price')
        )['total'] or 0,
        'total_clients': Property.objects.values('bookings__client').distinct().count()
    }
    
    return JsonResponse(stats)
