from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, permissions
from .models import ClientProfile
from .serializers import ClientProfileSerializer
from properties.models import CustomUser
from django.db.models import Count, Sum, Avg, F

class ClientProfileViewSet(viewsets.ModelViewSet):
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

@login_required
def clients_list(request):
    # Get all clients with their booking stats
    clients = CustomUser.objects.filter(is_client=True).annotate(
        total_bookings=Count('bookings'),
        total_spent=Sum('bookings__total_price')
    )
    
    # Calculate overall stats
    total_clients = clients.count()
    stats = {
        'total_clients': total_clients,
        'active_clients': clients.filter(bookings__isnull=False).distinct().count(),
        'average_bookings': clients.aggregate(
            avg=Avg('total_bookings')
        )['avg'] or 0,
        'average_spent': clients.aggregate(
            avg=Avg('total_spent')
        )['avg'] or 0
    }
    
    context = {
        'clients': clients,
        'stats': stats
    }
    return render(request, 'clients.html', context)

@login_required
def client_profile(request, client_id):
    client = get_object_or_404(CustomUser, id=client_id, is_client=True)
    profile, created = ClientProfile.objects.get_or_create(user=client)
    
    if request.method == 'POST':
        profile.phone_number = request.POST.get('phone_number', '')
        profile.address = request.POST.get('address', '')
        profile.preferred_contact = request.POST.get('preferred_contact', 'email')
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('clients_list')
    
    context = {
        'client': client,
        'profile': profile,
        'bookings': client.bookings.all().order_by('-created_at')
    }
    return render(request, 'client_profile.html', context)

@login_required
def client_create(request):
    if request.method == 'POST':
        try:
            # Create user with client role
            user = CustomUser.objects.create_user(
                username=request.POST['username'],
                email=request.POST['email'],
                is_client=True
            )
            
            # Create client profile
            profile = ClientProfile.objects.create(
                user=user,
                phone_number=request.POST.get('phone_number', ''),
                address=request.POST.get('address', '')
            )
            
            messages.success(request, 'Client created successfully!')
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f'Error creating client: {str(e)}')
            return redirect('dashboard')
    return redirect('dashboard')
