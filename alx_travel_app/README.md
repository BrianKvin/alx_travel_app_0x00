# ALX Travel App 0x00

A Django-based Airbnb clone featuring property listings, bookings, and reviews with a REST API architecture.

## Project Structure

```
alx_travel_app/
├── listings/
│   ├── models.py              # Database models (Listing, Booking, Review)
│   ├── serializers.py         # DRF serializers for API endpoints
│   ├── management/
│   │   └── commands/
│   │       └── seed.py        # Database seeding command
│   └── ...
├── requirements.txt
└── README.md
```

## Models

### Listing Model
- **Primary Key**: UUID-based `listing_id`
- **Fields**: title, description, location, price_per_night, property_type, max_guests, bedrooms, bathrooms, amenities, availability status
- **Relationships**: Belongs to a host (User), has many bookings and reviews
- **Features**: Automatic timestamps, rating calculation, amenities parsing

### Booking Model
- **Primary Key**: UUID-based `booking_id`
- **Fields**: check-in/out dates, number of guests, total price, status (pending/