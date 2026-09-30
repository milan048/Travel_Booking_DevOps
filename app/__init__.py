import os
import logging
from flask import Flask, request, session, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from wtforms import SelectField, DateField, FloatField, StringField, SubmitField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms.validators import NumberRange

# Initialize the database instance globally
db = SQLAlchemy()


# Custom AdminIndexView with access control and custom buttons
class MyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if not self.is_accessible():
            return self.inaccessible_callback(name="index")
        return self.render("admin/index.html")  

    def is_accessible(self):
        return session.get("admin_logged_in")  # Check if admin is logged in

    def inaccessible_callback(self, name, **kwargs):
        flash("You must log in as admin to access the admin panel.", "warning")
        return redirect(url_for("routes.admin_login"))


# Custom ModelView for managing models in the admin panel
class MyModelView(ModelView):
    def is_accessible(self):
        return session.get("admin_logged_in")  # Check if admin is logged in

    def inaccessible_callback(self):
        flash("You must log in as admin to access the admin panel.", "warning")
        return redirect(url_for("routes.admin_login"))


# Custom SearchForm for searching in the admin panel


class SearchForm(FlaskForm):
    search_query = StringField("Search", validators=[DataRequired()])
    submit = SubmitField("Search")


from app.models import PackageDeal, Hotel, Flight, Booking, Contact, User

class BookingAdmin(ModelView):
    # Define searchable fields
    column_searchable_list = ["name", "email", "destination"]

    # Define all possible columns
    column_list = (
        "id",
        "name",
        "email",
        "service_type",
        "destination",
        "num_people",
        "total_price",
        "booking_date",
        "is_confirmed",
    )

    # Define filters
    column_filters = ["booking_date"]

    # Define column labels for better readability
    column_labels = {
        "service_type": "Service Type",
        "num_people": "Number of People",
        "total_price": "Total Price",
        "booking_date": "Booking Date",
        "is_confirmed": "Confirmed",
    }

    # Define form fields
    form_columns = (
        "name",
        "email",
        "destination",
        "service_type",
        "flight_id",
        "hotel_id",
        "package_deal_id",
        "num_people",
        "booking_date",
        "total_price",
        "is_confirmed",
    )

    form_extra_fields = {
        "service_type": SelectField(
            "Service Type",
            choices=[
                ("Flight", "Flight"),
                ("Hotel", "Hotel"),
                ("PackageDeal", "Package Deal"),
            ],
            validators=[DataRequired()],
        ),
        "flight_id": SelectField("Flight", choices=[], coerce=int, validators=[]),
        "hotel_id": SelectField("Hotel", choices=[], coerce=int, validators=[]),
        "package_deal_id": SelectField("Package Deal", choices=[], coerce=int, validators=[]),
    }

    # Dynamically populate select field choices for create/edit forms
    def _populate_service_choices(self, form):
        form.flight_id.choices = [(0, "None")] + [(f.id, f.airline) for f in Flight.query.all()]
        form.hotel_id.choices = [(0, "None")] + [(h.id, h.hotel_name) for h in Hotel.query.all()]
        form.package_deal_id.choices = [(0, "None")] + [(p.id, f"Package {p.id}") for p in PackageDeal.query.all()]

    def create_form(self, obj=None):
        form = super(BookingAdmin, self).create_form(obj)
        self._populate_service_choices(form)
        return form

    def edit_form(self, obj=None):
        form = super(BookingAdmin, self).edit_form(obj)
        self._populate_service_choices(form)
        return form

    # Handle form submissions to set the appropriate foreign keys based on service_type
    def on_model_change(self, form, model, is_created):
        try:
            # Reset foreign keys based on service_type
            model.flight_id = form.flight_id.data if form.service_type.data == "Flight" and form.flight_id.data != 0 else None
            model.hotel_id = form.hotel_id.data if form.service_type.data == "Hotel" and form.hotel_id.data != 0 else None
            model.package_deal_id = form.package_deal_id.data if form.service_type.data == "PackageDeal" and form.package_deal_id.data != 0 else None

            # Set service type
            model.service_type = form.service_type.data

            # Calculate total price
            model.total_price = model.calculate_total_price()  # Ensure this method exists and calculates correctly

            # Validate that required foreign keys are set based on service_type
            if form.service_type.data == "Flight" and not model.flight_id:
                raise ValueError("Flight ID must be set for Flight service type.")
            if form.service_type.data == "Hotel" and not model.hotel_id:
                raise ValueError("Hotel ID must be set for Hotel service type.")
            if form.service_type.data == "PackageDeal" and not model.package_deal_id:
                raise ValueError("Package Deal ID must be set for Package Deal service type.")

        except Exception as e:
            logger.error(f"Error in BookingAdmin.on_model_change: {e}")
            flash(f"Error processing booking: {e}", "danger")
            raise e

    def get_query(self):
        # Get the current query
        query = super().get_query()
        # Check if service_type is in the request args
        service_type = request.args.get("service_type")
        if service_type:
            query = query.filter_by(service_type=service_type)
        return query

    def get_count_query(self):
        # Get the count query for pagination
        query = super().get_count_query()
        # Check if service_type is in the request args
        service_type = request.args.get("service_type")
        if service_type:
            query = query.filter_by(service_type=service_type)
        return query

class BaseBookingAdmin(BookingAdmin):
    def get_query(self):
        return super().get_query().filter(Booking.service_type == self.service_type)

    def get_count_query(self):
        return super().get_count_query().filter(Booking.service_type == self.service_type)


class FlightBookingAdmin(BaseBookingAdmin):
    service_type = 'Flight'
    
    column_list = BookingAdmin.column_list + (
        "flight.airline",
        "flight_number",
        "flight.departure_time",
        "flight.arrival_time",
    )
    
    form_columns = BookingAdmin.form_columns + ("flight_id",)


class HotelBookingAdmin(BaseBookingAdmin):
    service_type = 'Hotel'
    
    column_list = BookingAdmin.column_list + (
        "hotel.hotel_name",
        "hotel.hotel_location",
        "hotel.checkin_date",
        "hotel.checkout_date",
    )
    
    form_columns = BookingAdmin.form_columns + ("hotel_id",)


class PackageDealBookingAdmin(BaseBookingAdmin):
    service_type = 'PackageDeal'
    
    column_list = BookingAdmin.column_list + (
        "package_deal.flight.airline",
        "package_deal.hotel.hotel_name",
    )
    
    form_columns = BookingAdmin.form_columns + ("package_deal_id",)


class UserAdmin(MyModelView):
    column_searchable_list = ["name", "email"]
    column_list = ("id", "name", "email", "password_hash")  # Adjusted field name
    column_labels = {"name": "Name", "email": "Email", "password_hash": "password"}

    form_columns = ("name", "email", "password_hash")

    def on_model_change(self, form, model, is_created):
        # Hash the password_hash before storing
        if form.password_hash.data:
            model.set_password_hash(
                form.password_hash.data
            )  # Assuming set_password_hash method exists

class FlightAdmin(ModelView):
    # List all fields to display in the table view
    column_list = (
        "id",
        "airline",
        "flight_number",
        "departure_city",
        "destination",
        "departure_time",
        "arrival_time",
        "price",
        "availability",
    )

    # Searchable fields in the table view
    column_searchable_list = [
        "airline",
        "flight_number",
        "departure_city",
        "destination",
    ]

    # Fields to filter by in the table view
    column_filters = [
        "airline",
        "departure_city",
        "destination",
        "departure_time",
        "arrival_time",
    ]

    # Custom labels for each column
    column_labels = {
        "airline": "Airline",
        "flight_number": "Flight Number",
        "departure_city": "Departure City",
        "destination": "Destination",
        "departure_time": "Departure Time",
        "arrival_time": "Arrival Time",
        "price": "Price",
        "availability": "Availability",
    }

    # Ensure the price field is available in the form when creating/editing a flight
    form_columns = [
        "airline",
        "flight_number",
        "departure_city",
        "destination",
        "departure_time",
        "arrival_time",
        "price",
        "availability",
    ]

    # Custom formatter for displaying price in Indian Rupees
    def _price_formatter(view, context, model, name):
        """Display the price description in Indian Rupees."""
        return f"₹{model.price:.2f}"

    # Assign the price formatter to the price column
    column_formatters = {"price": _price_formatter}


class HotelAdmin(ModelView):
    # List all fields to display in the table view
    column_list = (
        "id",
        "hotel_name",
        "hotel_location",
        "hotel_rating",
        "checkin_date",
        "checkout_date",
        "price",
        "availability",
    )

    # Searchable fields in the table view
    column_searchable_list = ["hotel_name", "hotel_location"]

    # Fields to filter by in the table view
    column_filters = ["hotel_location", "hotel_rating", "checkin_date", "checkout_date"]

    # Custom labels for each column
    column_labels = {
        "hotel_name": "Hotel Name",
        "hotel_location": "Hotel Location",
        "hotel_rating": "Hotel Rating",
        "checkin_date": "Check-in Date",
        "checkout_date": "Check-out Date",
        "price": "Price",
        "availability": "Availability",
    }

    # Ensure the price field is available in the form when creating/editing a hotel
    form_columns = [
        "hotel_name",
        "hotel_location",
        "hotel_rating",
        "checkin_date",
        "checkout_date",
        "price",
        "availability",
    ]

    # Custom formatter for displaying price in Indian Rupees
    def _price_formatter(view, context, model, name):
        """Display the price description in Indian Rupees."""
        return f"₹{model.price:.2f}"

    # Assign the price formatter to the price column
    column_formatters = {"price": _price_formatter}


class PackageDealAdmin(ModelView):
    # Define the columns to display in the list view
    column_list = (
        "id",
        "flight_airline",
        "hotel_name",
        "start_date",
        "end_date",
        "price",
        "flight_availability",
        "hotel_availability",
    )

    column_labels = {
        "flight_airline": "Flight Airline",
        "hotel_name": "Hotel Name",
        "start_date": "Start Date",
        "end_date": "End Date",
        "price": "Price",
        "flight_availability": "Flight Availability",
        "hotel_availability": "Hotel Availability",
    }

    form_columns = (
        "flight_id",
        "hotel_id",
        "start_date",
        "end_date",
        "price",
    )

    form_extra_fields = {
        "flight_id": SelectField(
            "Flight", choices=[], coerce=int, validators=[DataRequired()]
        ),
        "hotel_id": SelectField(
            "Hotel", choices=[], coerce=int, validators=[DataRequired()]
        ),
        "start_date": DateField(
            "Start Date", format="%Y-%m-%d", validators=[DataRequired()]
        ),
        "end_date": DateField(
            "End Date", format="%Y-%m-%d", validators=[DataRequired()]
        ),
        "price": FloatField(
            "Price",
            validators=[
                DataRequired(),
                NumberRange(min=0.0, message="Price must be a positive number."),
            ],
        ),
    }

    # Custom formatter for displaying price in Indian Rupees
    def _price_formatter(view, context, model, name):
        """Display the price in a formatted manner in Indian Rupees."""
        return f"₹{model.price:.2f}"

    column_formatters = {
        "price": _price_formatter,
        "flight_airline": lambda v, c, m, n: m.flight.airline if m.flight else "N/A",
        "hotel_name": lambda v, c, m, n: m.hotel.hotel_name if m.hotel else "N/A",
        "flight_availability": lambda v, c, m, n: "Available" if m.flight.availability else "Unavailable",
        "hotel_availability": lambda v, c, m, n: "Available" if m.hotel.availability else "Unavailable",
    }

    def create_form(self, obj=None):
        form = super().create_form(obj)
        form.flight_id.choices = [(f.id, f.airline) for f in Flight.query.all()]
        form.hotel_id.choices = [(h.id, h.hotel_name) for h in Hotel.query.all()]
        return form

    def edit_form(self, obj=None):
        form = super().edit_form(obj)
        form.flight_id.choices = [(f.id, f.airline) for f in Flight.query.all()]
        form.hotel_id.choices = [(h.id, h.hotel_name) for h in Hotel.query.all()]
        return form

    def get_query(self):
        return super().get_query().join(Flight).join(Hotel)

    def get_count_query(self):
        return super().get_count_query().join(Flight).join(Hotel)

def seed_demo_data():
    """Create small demo inventory so a fresh checkout is immediately usable."""
    from datetime import datetime, date, timedelta
    from app.models import Flight, Hotel, PackageDeal

    if Flight.query.count() == 0:
        today = datetime.utcnow()
        flights = [
            Flight(60, 5500, "IndiGo", "Mumbai", "Goa", today + timedelta(days=7), today + timedelta(days=8), "6E-201"),
            Flight(45, 6200, "Air India", "Mumbai", "Delhi", today + timedelta(days=10), today + timedelta(days=10), "AI-101"),
            Flight(50, 4800, "Akasa Air", "Mumbai", "Jaipur", today + timedelta(days=14), today + timedelta(days=14), "QP-145"),
            Flight(40, 7000, "Vistara", "Delhi", "Manali", today + timedelta(days=20), today + timedelta(days=20), "UK-705"),
        ]
        db.session.add_all(flights)
        db.session.flush()

    if Hotel.query.count() == 0:
        today = datetime.utcnow()
        hotels = [
            Hotel(30, 3200, "Goa Beach Resort", "Goa", 4, today + timedelta(days=1), today + timedelta(days=30)),
            Hotel(25, 2800, "Delhi Central Hotel", "Delhi", 4, today + timedelta(days=1), today + timedelta(days=30)),
            Hotel(20, 3000, "Jaipur Palace Stay", "Jaipur", 5, today + timedelta(days=1), today + timedelta(days=30)),
            Hotel(20, 3500, "Manali Mountain Resort", "Manali", 4, today + timedelta(days=1), today + timedelta(days=30)),
        ]
        db.session.add_all(hotels)
        db.session.flush()

    if PackageDeal.query.count() == 0:
        flights = Flight.query.all()
        hotels = Hotel.query.all()
        by_destination = {f.destination.lower(): f for f in flights}
        by_location = {h.hotel_location.lower(): h for h in hotels}
        packages=[]
        for destination in ("Goa", "Delhi", "Jaipur", "Manali"):
            f=by_destination.get(destination.lower())
            h=by_location.get(destination.lower())
            if f and h:
                start=date.today()+timedelta(days=15)
                packages.append(PackageDeal(f.id,h.id,start,start+timedelta(days=4),f.price+h.price+1500))
        db.session.add_all(packages)
    db.session.commit()


def create_app():
    app = Flask(__name__)

    # App configurations
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///Travelbookingsystem.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s %(message)s")
    # Initialize the database and Flask-Migrate with the app
    db.init_app(app)
    from . import (
        MyAdminIndexView,
        UserAdmin,
        BookingAdmin,
        MyModelView,
        HotelAdmin,
        FlightAdmin,
        PackageDealAdmin,
    )

    admin = Admin(
        app,
        name="Admin Panel",
        index_view=MyAdminIndexView(),
        template_mode="bootstrap3",
    )

    # Push the app context before performing operations like adding admin views
    with app.app_context():
        # Ensure tables are created
        db.create_all()
        seed_demo_data()

        # Add views for managing User, Booking, Contact, Hotel, Flight, PackageDeal models
        admin.add_view(UserAdmin(User, db.session))
        admin.add_view(BookingAdmin(Booking, db.session))
        admin.add_view(
            FlightBookingAdmin(
                Booking, db.session, name="Flight Bookings", endpoint="flight_bookings"
            )
        )
        admin.add_view(
            HotelBookingAdmin(
                Booking, db.session, name="Hotel Bookings", endpoint="hotel_bookings"
            )
        )
        admin.add_view(
            PackageDealBookingAdmin(
                Booking,
                db.session,
                name="Package Deal Bookings",
                endpoint="package_deal_bookings",
            )
        )
        admin.add_view(MyModelView(Contact, db.session))
        admin.add_view(HotelAdmin(Hotel, db.session))
        admin.add_view(FlightAdmin(Flight, db.session))
        admin.add_view(PackageDealAdmin(PackageDeal, db.session))
    # Register the blueprint (after initializing the app and db)
    from .views import bp

    app.register_blueprint(bp)
    

    @app.get("/health")
    def health():
        return {"status": "UP", "service": "travel-booking"}, 200

    @app.get("/metrics")
    def metrics():
        body = "# HELP travel_booking_up Application health\n# TYPE travel_booking_up gauge\ntravel_booking_up 1\n"
        return Response(body, mimetype="text/plain")

    return app
