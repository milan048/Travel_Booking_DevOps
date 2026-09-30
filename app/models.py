from datetime import datetime
from app import db
from app.services import register_service
from sqlalchemy.orm import validates
from werkzeug.security import generate_password_hash,check_password_hash
from app.metaclass import ServiceMeta

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        """Hashes the password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password_hash, password)

class Booking(db.Model):
    __tablename__ = 'booking' 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  
    email = db.Column(db.String(120), nullable=False)  
    destination = db.Column(db.String(60), nullable=False)  
    booking_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    num_people = db.Column(db.Integer, nullable=False)  
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  
    flight_number = db.Column(db.String(50), nullable=True)
    total_price = db.Column(db.Integer, nullable=False)
    service_type = db.Column(db.String(50), nullable=False)  
    flight_id = db.Column(db.Integer, db.ForeignKey('flight.id'), nullable=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=True)
    package_deal_id = db.Column(db.Integer, db.ForeignKey('package_deal.id'), nullable=True)
    flight = db.relationship('Flight', backref='bookings', lazy=True)
    hotel = db.relationship('Hotel', backref='bookings', lazy=True)
    package_deal = db.relationship('PackageDeal', backref='bookings', lazy=True)
    
    # New status field - default to 'confirmed'
    is_confirmed = db.Column(db.Boolean, default=True, nullable=False)

    def calculate_total_price(self):
        if self.service_type == 'Flight' and self.flight:
            return self.flight.calculate_cost() * self.num_people
        elif self.service_type == 'Hotel' and self.hotel:
            return self.hotel.calculate_cost() * self.num_people
        elif self.service_type == 'PackageDeal' and self.package_deal:
            return self.package_deal.calculate_cost() * self.num_people
        else:
            return 0

    def cancel_booking(self):
        """Cancel the booking by setting is_confirmed to False."""
        self.is_confirmed = False

    def confirm_booking(self):
        """Confirm the booking by setting is_confirmed to True."""
        self.is_confirmed = True

    def __repr__(self):
        status = "Confirmed" if self.is_confirmed else "Canceled"
        return f'<Booking {self.id} for {self.user.name} ({status})>'

class Contact(db.Model):
    __tablename__ = 'contact' 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Contact {self.name}>'

class TravelService(db.Model):
    __metaclass__ = ServiceMeta
    __abstract__ = True 
    id = db.Column(db.Integer, primary_key=True)
    availability = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  
    def __init__(self, availability, price):
        self.availability = availability
        self.price = price

    @validates('price')
    def validate_price(self, key, value):
        if value is not None and value < 0:
            raise ValueError("Price cannot be negative.")
        return value

    def calculate_cost(self):
        """To be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement this method")

    def __repr__(self):
        return f"<TravelService(id={self.id}, availability={self.availability}, price={self.price})>"

@register_service
class Flight(TravelService):
    __tablename__ = 'flight' 

    airline = db.Column(db.String(120), nullable=False)
    departure_city = db.Column(db.String(120), nullable=False)
    destination = db.Column(db.String(120), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    flight_number = db.Column(db.String(120), nullable=False)
    
    @validates('price') 
    def validate_price(self, key, value):
        if value is not None and value < 0:
            raise ValueError("Price cannot be negative.")
        return value

    def __init__(self, availability, price, airline, departure_city, destination, departure_time, arrival_time, flight_number):
        super().__init__(availability, price)
        self.airline = airline
        self.departure_city = departure_city
        self.destination = destination
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.flight_number = flight_number

    def calculate_cost(self):
        return self.price * 1.2  # Add 20% tax

    def __repr__(self):
        return f"<Flight(airline={self.airline}, id={self.id})>"
    
@register_service
class Hotel(TravelService):
    __tablename__ = 'hotel'  # Explicitly define table name

    hotel_name = db.Column(db.String(120), nullable=False)
    hotel_location = db.Column(db.String(120), nullable=False)
    hotel_rating = db.Column(db.Integer, nullable=False)
    checkin_date = db.Column(db.DateTime, nullable=False)
    checkout_date = db.Column(db.DateTime, nullable=False)
    
    @validates('price') 
    def validate_price(self, key, value):
        if value is not None and value < 0:
            raise ValueError("Price cannot be negative.")
        return value
  
    def __init__(self, availability, price, hotel_name, hotel_location, hotel_rating, checkin_date, checkout_date):
        super().__init__(availability, price)
        self.hotel_name = hotel_name
        self.hotel_location = hotel_location
        self.hotel_rating = hotel_rating
        self.checkin_date = checkin_date
        self.checkout_date = checkout_date

    def calculate_cost(self):
        return self.price * 1.1  # Add 10% service charge

    def __repr__(self):
        return f"<Hotel(hotel_name={self.hotel_name}, id={self.id})>"

@register_service
class PackageDeal(db.Model):
    __tablename__ = 'package_deal'

    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flight.id'), nullable=False)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)  
    end_date = db.Column(db.Date, nullable=False)   
    price = db.Column(db.Float, nullable=False)  
    
    flight = db.relationship('Flight', backref='package_deals', lazy=True)
    hotel = db.relationship('Hotel', backref='package_deals', lazy=True)

    @validates('price') 
    def validate_price(self, key, value):
        if value is not None and value < 0:
            raise ValueError("Price cannot be negative.")
        return value

    def __init__(self, flight_id, hotel_id, start_date, end_date, price):
        self.flight_id = flight_id
        self.hotel_id = hotel_id
        self.start_date = start_date
        self.end_date = end_date
        self.price = price 

    def calculate_cost(self):
        return self.flight.calculate_cost() + self.hotel.calculate_cost()

    def __repr__(self):
        return (f"<PackageDeal(flight={self.flight.airline}, hotel={self.hotel.hotel_name}, "
                f"start_date={self.start_date}, end_date={self.end_date})>")

    @property
    def availability(self):
        """Calculate availability based on flight and hotel availability.""" 
        return min(self.flight.availability, self.hotel.availability)
