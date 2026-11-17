from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
def hello_world(request):
    """
    Simple API endpoint that returns a greeting.
    """
    data = {
        'message': 'Hello from Django API!',
        'status': 'success',
        'data': {
            'project': 'Vang Vieng Stay',
            'version': '1.0.0',
        }
    }
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_guesthouse_count(request):
    """
    Returns the total number of guesthouses.
    """
    from guesthouse.models import Guesthouse
    
    count = Guesthouse.objects.count()
    
    data = {
        'message': 'Guesthouse count retrieved successfully',
        'count': count,
    }
    return Response(data, status=status.HTTP_200_OK)