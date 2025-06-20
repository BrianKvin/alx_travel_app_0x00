from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Listing, Booking, Review


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class ListingSerializer(serializers.ModelSerializer):
    """Serializer for Listing model"""
    
    host = UserSerializer(read_only=True)
    amenities_list = serializers.ReadOnlyField(source='get_amenities_list')
    average_rating = serializers.ReadOnlyField()
    total_reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Listing
        fields = [
            'listing_id', 'host', 'title', 'description', 'location',
            'price_per_night', 'property_type', 'max_guests', 'bedrooms',
            'bathrooms', 'amenities', 'amenities_list', 'available',
            'average_rating', 'total_reviews', 'created_at', 'updated_at'
        ]
        read_only_fields = ['listing_id', 'created_at', 'updated_at']
    
    def get_total_reviews(self, obj):
        """Get total number of reviews for the listing"""
        return obj.reviews.count()
    
    def validate_price_per_night(self, value):
        """Validate price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Price per night must be greater than 0")
        return value
    
    def validate_max_guests(self, value):
        """Validate max_guests is positive"""
        if value <= 0:
            raise serializers.ValidationError("Maximum guests must be at least 1")
        return value


class ListingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating listings (without read-only fields)"""
    
    class Meta:
        model = Listing
        fields = [
            'title', 'description', 'location', 'price_per_night',
            'property_type', 'max_guests', 'bedrooms', 'bathrooms',
            'amenities', 'available'
        ]
    
    def create(self, validated_data):
        """Create listing with authenticated user as host"""
        validated_data['host'] = self.context['request'].user
        return super().create(validated_data)


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for Booking model"""
    
    listing = ListingSerializer(read_only=True)
    guest = UserSerializer(read_only=True)
    listing_id = serializers.UUIDField(write_only=True)
    duration_days = serializers.ReadOnlyField()
    
    class Meta:
        model = Booking
        fields = [
            'booking_id', 'listing', 'listing_id', 'guest', 'check_in_date',
            'check_out_date', 'number_of_guests', 'total_price', 'status',
            'duration_days', 'created_at', 'updated_at'
        ]
        read_only_fields = ['booking_id', 'total_price', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate booking data"""
        from datetime import date
        
        # Validate dates
        if data['check_out_date'] <= data['check_in_date']:
            raise serializers.ValidationError(
                "Check-out date must be after check-in date"
            )
        
        # Validate check-in date is not in the past
        if data['check_in_date'] < date.today():
            raise serializers.ValidationError(
                "Check-in date cannot be in the past"
            )
        
        # Validate listing exists and get it
        try:
            listing = Listing.objects.get(listing_id=data['listing_id'])
        except Listing.DoesNotExist:
            raise serializers.ValidationError("Listing not found")
        
        # Validate number of guests
        if data['number_of_guests'] > listing.max_guests:
            raise serializers.ValidationError(
                f"Number of guests ({data['number_of_guests']}) exceeds "
                f"maximum allowed ({listing.max_guests})"
            )
        
        # Validate listing is available
        if not listing.available:
            raise serializers.ValidationError("Listing is not available")
        
        # Check for overlapping bookings
        overlapping_bookings = Booking.objects.filter(
            listing=listing,
            status__in=['confirmed', 'pending'],
            check_in_date__lt=data['check_out_date'],
            check_out_date__gt=data['check_in_date']
        )
        
        if overlapping_bookings.exists():
            raise serializers.ValidationError(
                "Listing is already booked for the selected dates"
            )
        
        return data
    
    def create(self, validated_data):
        """Create booking with calculated total price"""
        listing_id = validated_data.pop('listing_id')
        listing = Listing.objects.get(listing_id=listing_id)
        
        # Calculate total price
        duration = (validated_data['check_out_date'] - validated_data['check_in_date']).days
        total_price = listing.price_per_night * duration
        
        validated_data['listing'] = listing
        validated_data['guest'] = self.context['request'].user
        validated_data['total_price'] = total_price
        
        return super().create(validated_data)


class BookingCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating bookings"""
    
    listing_id = serializers.UUIDField()
    
    class Meta:
        model = Booking
        fields = [
            'listing_id', 'check_in_date', 'check_out_date', 'number_of_guests'
        ]


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model"""
    
    guest = UserSerializer(read_only=True)
    listing = ListingSerializer(read_only=True)
    listing_id = serializers.UUIDField(write_only=True)
    booking_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = Review
        fields = [
            'review_id', 'listing', 'listing_id', 'guest', 'booking_id',
            'rating', 'comment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['review_id', 'created_at', 'updated_at']
    
    def validate_rating(self, value):
        """Validate rating is between 1 and 5"""
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
    
    def validate(self, data):
        """Validate review data"""
        # Validate listing exists
        try:
            listing = Listing.objects.get(listing_id=data['listing_id'])
        except Listing.DoesNotExist:
            raise serializers.ValidationError("Listing not found")
        
        # Validate user has a completed booking for this listing
        guest = self.context['request'].user
        completed_bookings = Booking.objects.filter(
            listing=listing,
            guest=guest,
            status='completed'
        )
        
        if not completed_bookings.exists():
            raise serializers.ValidationError(
                "You can only review listings you have stayed at"
            )
        
        # Check if user already reviewed this listing
        existing_review = Review.objects.filter(
            listing=listing,
            guest=guest
        ).first()
        
        if existing_review and not self.instance:
            raise serializers.ValidationError(
                "You have already reviewed this listing"
            )
        
        return data
    
    def create(self, validated_data):
        """Create review"""
        listing_id = validated_data.pop('listing_id')
        booking_id = validated_data.pop('booking_id', None)
        
        listing = Listing.objects.get(listing_id=listing_id)
        validated_data['listing'] = listing
        validated_data['guest'] = self.context['request'].user
        
        if booking_id:
            try:
                booking = Booking.objects.get(booking_id=booking_id)
                validated_data['booking'] = booking
            except Booking.DoesNotExist:
                pass
        
        return super().create(validated_data)


class ListingSummarySerializer(serializers.ModelSerializer):
    """Simplified serializer for listing summaries"""
    
    host_name = serializers.CharField(source='host.username', read_only=True)
    average_rating = serializers.ReadOnlyField()
    total_reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Listing
        fields = [
            'listing_id', 'title', 'location', 'price_per_night',
            'property_type', 'max_guests', 'host_name', 'average_rating',
            'total_reviews', 'available'
        ]
    
    def get_total_reviews(self, obj):
        return obj.reviews.count()