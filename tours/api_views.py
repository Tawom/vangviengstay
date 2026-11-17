from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Tour
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