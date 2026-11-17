from rest_framework import serializers
from .models import Tour


class TourSerializer(serializers.ModelSerializer):
    """
    Converts Tour model instances into JSON format.
    """
    # Add computed properties as read-only fields
    average_rating = serializers.ReadOnlyField()
    review_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Tour
        fields = [
            'id',
            'name',
            'operator_name',
            'description_en',
            'description_lo',
            'price_per_person',
            'duration_hours',
            'max_capacity',
            'departure_time',
            'main_image_url',
            'latitude',
            'longitude',
            'average_rating',
            'review_count',
            'is_active',
        ]