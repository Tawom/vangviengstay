from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Tour, TourBooking
from .serializers import TourSerializer


@api_view(['GET'])
def tour_list(request):
    """Returns a list of all active tours."""
    tours = Tour.objects.filter(is_active=True)
    serializer = TourSerializer(tours, many=True)
    
    return Response({
        'message': 'Tours retrieved successfully',
        'count': len(serializer.data),
        'tours': serializer.data,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def tour_detail(request, pk):
    """Returns details for a single tour by its ID (pk)."""
    try:
        tour = Tour.objects.get(pk=pk, is_active=True)
        serializer = TourSerializer(tour)
        
        return Response({
            'message': 'Tour retrieved successfully',
            'tour': serializer.data,
        }, status=status.HTTP_200_OK)
        
    except Tour.DoesNotExist:
        return Response({
            'message': 'Tour not found',
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def create_booking(request, tour_id):
    """Handle tour booking submissions from Flutter/Web."""
    try:
        tour = Tour.objects.get(id=tour_id, is_active=True)
    except Tour.DoesNotExist:
        return Response({'error': 'Tour not found'}, status=status.HTTP_404_NOT_FOUND)

    # Extract data from Flutter request
    data = request.data
    booking_date_str = data.get('booking_date')
    number_of_people = int(data.get('number_of_people', 1))
    pickup_option = data.get('pickup_option', 'self')
    pickup_location = data.get('pickup_location', '')
    contact_name = data.get('contact_name', 'Guest')
    contact_phone = data.get('contact_phone', '')
    contact_email = data.get('contact_email', '')

    # Basic validation
    if not contact_phone and not contact_email:
        return Response(
            {'error': 'Please provide either a phone number or email.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Create the booking
        booking = TourBooking.objects.create(
            tour=tour,
            guest=None,  # Guest checkout
            booking_date=booking_date_str,
            number_of_people=number_of_people,
            total_price=number_of_people * float(tour.price_per_person),
            status='pending',
            pickup_option=pickup_option,
            pickup_location=pickup_location if pickup_option == 'vehicle' else '',
            contact_phone=contact_phone,
            contact_email=contact_email,
        )

        # TODO: Trigger email confirmation here
        # from advisor.email_utils import send_booking_confirmation_email
        # send_booking_confirmation_email(booking, contact_name)

        return Response({
            'message': 'Booking created successfully!',
            'booking_id': booking.id,
            'total_price': str(booking.total_price)
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)