from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from listings.models import Listing, Booking, Review
from decimal import Decimal
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Seed the database with sample listings, bookings, and reviews'

    def add_arguments(self, parser):
        parser.add_argument(
            '--listings',
            type=int,
            default=20,
            help='Number of listings to create (default: 20)'
        )
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of users to create (default: 10)'
        )
        parser.add_argument(
            '--bookings',
            type=int,
            default=30,
            help='Number of bookings to create (default: 30)'
        )
        parser.add_argument(
            '--reviews',
            type=int,
            default=25,
            help='Number of reviews to create (default: 25)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(
                self.style.WARNING('Clearing existing data...')
            )
            Review.objects.all().delete()
            Booking.objects.all().delete()
            Listing.objects.all().delete()
            # Don't delete superuser accounts
            User.objects.filter(is_superuser=False).delete()

        # Create users
        self.stdout.write('Creating users...')
        users = self.create_users(options['users'])
        
        # Create listings
        self.stdout.write('Creating listings...')
        listings = self.create_listings(options['listings'], users)
        
        # Create bookings
        self.stdout.write('Creating bookings...')
        bookings = self.create_bookings(options['bookings'], listings, users)
        
        # Create reviews
        self.stdout.write('Creating reviews...')
        self.create_reviews(options['reviews'], bookings)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded database with:\n'
                f'- {len(users)} users\n'
                f'- {len(listings)} listings\n'
                f'- {len(bookings)} bookings\n'
                f'- {options["reviews"]} reviews'
            )
        )

    def create_users(self, count):
        """Create sample users"""
        users = []
        
        # Sample user data
        first_names = [
            'John', 'Jane', 'Michael', 'Sarah', 'David', 'Emma', 'Chris', 'Lisa',
            'Robert', 'Anna', 'James', 'Maria', 'William', 'Jennifer', 'Daniel'
        ]
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
            'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez'
        ]
        
        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f"{first_name.lower()}{last_name.lower()}{i+1}"
            email = f"{username}@example.com"
            
            # Check if user already exists
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password='password123'
                )
                users.append(user)
        
        return users

    def create_listings(self, count, users):
        """Create sample listings"""
        listings = []
        
        # Sample listing data
        property_types = ['apartment', 'house', 'condo', 'villa', 'cabin', 'loft', 'studio']
        cities = [
            'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia',
            'San Antonio', 'San Diego', 'Dallas', 'San Jose', 'Austin', 'Jacksonville',
            'Fort Worth', 'Columbus', 'Charlotte', 'San Francisco', 'Indianapolis',
            'Seattle', 'Denver', 'Washington DC', 'Boston', 'Nashville', 'Portland',
            'Las Vegas', 'Detroit', 'Memphis', 'Louisville', 'Baltimore', 'Milwaukee'
        ]
        
        amenities_options = [
            'WiFi,Air Conditioning,Kitchen,Parking',
            'WiFi,Pool,Gym,Balcony',
            'WiFi,Kitchen,Washer,Dryer,Parking',
            'WiFi,Hot Tub,Fireplace,Garden',
            'WiFi,Beach Access,Kitchen,BBQ',
            'WiFi,Mountain View,Hiking Trails,Kitchen',
            'WiFi,City View,Elevator,Concierge',
            'WiFi,Pet Friendly,Garden,Parking',
            'WiFi,Waterfront,Boat Dock,Kitchen',
            'WiFi,Ski Access,Fireplace,Hot Tub'
        ]
        
        titles_templates = [
            "Cozy {property_type} in {city}",
            "Modern {property_type} with great view",
            "Spacious {property_type} in downtown {city}",
            "Beautiful {property_type} near attractions",
            "Luxury {property_type} in {city} center",
            "Charming {property_type} with all amenities",
            "Stunning {property_type} perfect for families",
            "Elegant {property_type} in quiet neighborhood",
            "Contemporary {property_type} with style",
            "Comfortable {property_type} for your stay"
        ]
        
        descriptions = [
            "Perfect for travelers looking for comfort and convenience. This property offers all the amenities you need for a memorable stay.",
            "A beautifully designed space that combines modern comfort with local charm. Ideal for both business and leisure travelers.",
            "Enjoy your stay in this well-appointed property featuring contemporary amenities and easy access to local attractions.",
            "This delightful property provides a peaceful retreat while keeping you close to the city's best dining and entertainment options.",
            "Experience luxury and comfort in this thoughtfully designed space, perfect for creating lasting memories with family and friends.",
            "A stylish and comfortable property that serves as your perfect home base for exploring the local area and attractions.",
            "This property combines convenience with comfort, offering everything you need for a relaxing and enjoyable stay.",
            "Discover this gem that offers both tranquility and accessibility, making it perfect for all types of travelers.",
        ]
        
        for i in range(count):
            property_type = random.choice(property_types)
            city = random.choice(cities)
            host = random.choice(users)
            
            title = random.choice(titles_templates).format(
                property_type=property_type.title(),
                city=city
            )
            
            listing = Listing.objects.create(
                host=host,
                title=title,
                description=random.choice(descriptions),
                location=f"{city}, {random.choice(['NY', 'CA', 'TX', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI'])}",
                price_per_night=Decimal(str(random.randint(50, 500))),
                property_type=property_type,
                max_guests=random.randint(1, 8),
                bedrooms=random.randint(1, 4),
                bathrooms=random.randint(1, 3),
                amenities=random.choice(amenities_options),
                available=random.choice([True, True, True, False])  # 75% available
            )
            listings.append(listing)
        
        return listings

    def create_bookings(self, count, listings, users):
        """Create sample bookings"""
        bookings = []
        statuses = ['pending', 'confirmed', 'cancelled', 'completed']
        status_weights = [0.1, 0.3, 0.1, 0.5]  # More completed bookings for reviews
        
        for i in range(count):
            listing = random.choice(listings)
            guest = random.choice([u for u in users if u != listing.host])  # Guest can't be host
            
            # Generate random dates
            start_date = date.today() - timedelta(days=random.randint(0, 180))
            duration = random.randint(1, 14)
            end_date = start_date + timedelta(days=duration)
            
            # Ensure booking doesn't exceed max guests
            num_guests = random.randint(1, min(listing.max_guests, 6))
            
            # Calculate total price
            total_price = listing.price_per_night * duration
            
            # Choose status based on dates
            if end_date < date.today():
                status = random.choices(['completed', 'cancelled'], weights=[0.8, 0.2])[0]
            elif start_date <= date.today() <= end_date:
                status = 'confirmed'
            else:
                status = random.choices(statuses, weights=status_weights)[0]
            
            try:
                booking = Booking.objects.create(
                    listing=listing,
                    guest=guest,
                    check_in_date=start_date,
                    check_out_date=end_date,
                    number_of_guests=num_guests,
                    total_price=total_price,
                    status=status
                )
                bookings.append(booking)
            except Exception as e:
                # Skip if there's a conflict (overlapping dates, etc.)
                continue
        
        return bookings

    def create_reviews(self, count, bookings):
        """Create sample reviews"""
        # Only create reviews for completed bookings
        completed_bookings = [b for b in bookings if b.status == 'completed']
        
        comments = [
            "Great place to stay! Very clean and comfortable. Host was responsive and helpful.",
            "Perfect location with easy access to attractions. The amenities were exactly as described.",
            "Beautiful property with amazing views. Would definitely recommend to others!",
            "Comfortable and well-equipped. Everything we needed for our stay was provided.",
            "Lovely property in a quiet neighborhood. Easy check-in process and great communication.",
            "Exceeded our expectations! The space was even better than the photos showed.",
            "Good value for money. Clean, comfortable, and in a convenient location.",
            "Nice property with thoughtful touches. Host provided excellent local recommendations.",
            "Peaceful and relaxing stay. Perfect for a weekend getaway.",
            "Well-maintained property with modern amenities. Would stay here again!",
            "Decent stay overall. Property was as described and met our basic needs.",
            "Good experience. Host was accommodating and the location worked well for us.",
            "Clean and comfortable with good amenities. A few minor issues but overall positive.",
            "Pleasant stay with friendly host. Property has character and charm.",
            "Solid choice for the price. Nothing fancy but clean and functional."
        ]
        
        reviews_created = 0
        attempted_bookings = completed_bookings.copy()
        random.shuffle(attempted_bookings)
        
        for booking in attempted_bookings:
            if reviews_created >= count:
                break
                
            # Check if review already exists for this booking
            if hasattr(booking, 'review'):
                continue
            
            # Create review with rating correlated to comment sentiment
            comment = random.choice(comments)
            if "great" in comment.lower() or "perfect" in comment.lower() or "exceeded" in comment.lower():
                rating = random.randint(4, 5)
            elif "decent" in comment.lower() or "solid" in comment.lower() or "minor issues" in comment.lower():
                rating = random.randint(3, 4)
            else:
                rating = random.randint(3, 5)
            
            Review.objects.create(
                listing=booking.listing,
                guest=booking.guest,
                booking=booking,
                rating=rating,
                comment=comment
            )
            reviews_created += 1
        
        return reviews_created