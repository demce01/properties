// Handle property price calculations
function calculateBookingPrice() {
    const startDate = document.getElementById('start_date').value;
    const endDate = document.getElementById('end_date').value;
    const propertyId = document.getElementById('property').value;

    if (startDate && endDate && propertyId) {
        const start = new Date(startDate);
        const end = new Date(endDate);
        const nights = (end - start) / (1000 * 60 * 60 * 24);

        fetch(`/api/properties/${propertyId}/`)
            .then(response => response.json())
            .then(data => {
                const total = nights * data.price_per_night;
                document.getElementById('total_price').textContent = `$${total.toFixed(2)}`;
            });
    }
}

// Handle property deletion with confirmation
function deleteProperty(id) {
    Swal.fire({
        title: 'Are you sure?',
        text: "You won't be able to revert this!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, delete it!'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/api/properties/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            }).then(response => {
                if (response.ok) {
                    Swal.fire(
                        'Deleted!',
                        'Property has been deleted.',
                        'success'
                    ).then(() => {
                        window.location.reload();
                    });
                }
            });
        }
    });
}

// Handle booking cancellation with confirmation
function cancelBooking(id) {
    Swal.fire({
        title: 'Cancel Booking?',
        text: "Are you sure you want to cancel this booking?",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, cancel it!'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/api/bookings/${id}/cancel/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            }).then(response => {
                if (response.ok) {
                    Swal.fire(
                        'Cancelled!',
                        'Booking has been cancelled.',
                        'success'
                    ).then(() => {
                        window.location.reload();
                    });
                }
            });
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    var myModalEl = document.getElementById('addBookingModal')
    if (myModalEl) {
        new bootstrap.Modal(myModalEl, {
            backdrop: 'static',
            keyboard: false
        });
    }
    
    // Initialize date pickers
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        $(input).datepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            todayHighlight: true,
            startDate: new Date()
        });
    });

    // Initialize select2 for enhanced select boxes
    $('.form-select').select2({
        theme: 'bootstrap-5',
        width: '100%'
    });

    // Add booking form validation
    const bookingForm = document.querySelector('form[action="/bookings/create/"]');
    if (bookingForm) {
        bookingForm.addEventListener('submit', function(e) {
            const startDate = new Date(document.getElementById('start_date').value);
            const endDate = new Date(document.getElementById('end_date').value);

            if (endDate <= startDate) {
                e.preventDefault();
                Swal.fire(
                    'Invalid Dates',
                    'Check-out date must be after check-in date',
                    'error'
                );
            }
        });
    }
});

// Dashboard stats auto-refresh
function refreshDashboardStats() {
    fetch('/api/dashboard/stats/')
        .then(response => response.json())
        .then(data => {
            Object.keys(data).forEach(key => {
                const element = document.getElementById(`stat-${key}`);
                if (element) {
                    if (key.includes('revenue')) {
                        element.textContent = `$${parseFloat(data[key]).toFixed(2)}`;
                    } else {
                        element.textContent = data[key];
                    }
                }
            });
        });
}

// Refresh dashboard stats every minute
if (document.querySelector('.stat-card')) {
    setInterval(refreshDashboardStats, 60000);
}