from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Payment
from bookings.models import Booking
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from rest_framework import viewsets
from .models import Payment
from .serializers import PaymentSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

@login_required
def payments_list(request):
    # Get all payments with related bookings
    payments = Payment.objects.select_related(
        'booking', 
        'booking__property', 
        'booking__client'
    ).all()
    
    # Get statistics
    stats = {
        'total_revenue': Payment.objects.filter(
            status='Completed'
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0,
        'completed_payments': Payment.objects.filter(
            status='Completed'
        ).count(),
        'pending_payments': Payment.objects.filter(
            status='Pending'
        ).count(),
        'average_payment': Payment.objects.filter(
            status='Completed'
        ).aggregate(
            avg=Avg('amount')
        )['avg'] or 0
    }
    
    # Get unpaid bookings for the payment form
    unpaid_bookings = Booking.objects.filter(
        payment__isnull=True
    ).select_related('property', 'client')
    
    context = {
        'payments': payments,
        'stats': stats,
        'unpaid_bookings': unpaid_bookings,
    }
    return render(request, 'payments.html', context)

@login_required
def payment_create(request):
    if request.method == 'POST':
        try:
            booking = Booking.objects.get(id=request.POST.get('booking'))
            payment = Payment.objects.create(
                booking=booking,
                amount=request.POST.get('amount'),
                payment_method=request.POST.get('payment_method'),
                payment_date=timezone.now(),
                status='Pending'
            )
            messages.success(request, 'Payment recorded successfully!')
            return redirect('payments_list')
        except Exception as e:
            messages.error(request, f'Error recording payment: {str(e)}')
            return redirect('payments_list')

@login_required
def payment_complete(request, payment_id):
    try:
        payment = Payment.objects.get(id=payment_id)
        payment.status = 'Completed'
        payment.save()
        return JsonResponse({'status': 'success'})
    except Payment.DoesNotExist:
        return JsonResponse(
            {'status': 'error', 'message': 'Payment not found'}, 
            status=404
        )
    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'message': str(e)}, 
            status=500
        )

@login_required
def payment_details(request, payment_id):
    try:
        payment = Payment.objects.select_related(
            'booking', 
            'booking__property', 
            'booking__client'
        ).get(id=payment_id)
        
        data = {
            'id': payment.id,
            'amount': payment.amount,
            'payment_method': payment.payment_method,
            'payment_date': payment.payment_date,
            'status': payment.status,
            'booking': {
                'id': payment.booking.id,
                'property': {
                    'name': payment.booking.property.name
                },
                'client': {
                    'username': payment.booking.client.username
                }
            }
        }
        return JsonResponse(data)
    except Payment.DoesNotExist:
        return JsonResponse(
            {'error': 'Payment not found'}, 
            status=404
        )
