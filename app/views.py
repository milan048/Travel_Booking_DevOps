from asyncio.log import logger
from datetime import datetime, timedelta
from sqlite3 import IntegrityError
from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
    Blueprint,
)
from sqlalchemy import func
from app import db
from app.context_managers import BookingContext
from app.forms import (
    RegistrationForm,
    LoginForm,
    BookingForm,
    ContactForm,
    EditProfileForm,
    UpdateBookingForm
)
from app.models import Contact, Flight, Hotel, PackageDeal, User, Booking
from sqlalchemy.orm import joinedload
from app.builders import PackageDealBuilder
from app.decorators import login_required


# Initialize the blueprint
bp = Blueprint("routes", __name__)


@bp.route("/")
def home():
    return render_template("home.html")


@bp.route("/about")
def about():
    return render_template("about.html")


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()  

    if form.validate_on_submit():  # If form is valid and submitted
        # Create a new contact entry
        new_contact = Contact(
            name=form.name.data,
            email=form.email.data,
            subject=form.subject.data,
            message=form.message.data,
        )

        # Save to the database
        try:
            db.session.add(new_contact)
            db.session.commit()
            flash("Your message has been sent successfully!", "success")
        except Exception as e:
            db.session.rollback()  # Rollback the transaction if something goes wrong
            flash(f"An error occurred: {e}", "danger")
            return redirect(url_for("routes.contact"))

        return redirect(url_for("routes.contact"))

    # For GET request or if form validation fails, render the contact form
    return render_template("contact.html", form=form)


@bp.route("/profile")
def profile():
    user_id = session.get("user_id")
    if user_id:
        user = User.query.get(user_id)
        bookings = Booking.query.filter_by(user_id=user.id).all()
        return render_template("profile.html", user=user, bookings=bookings)
    return redirect(url_for("routes.login"))


@bp.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():
    user_id = session.get("user_id")

    if not user_id:
        flash("User is not logged in.", "danger")
        return redirect(url_for("routes.home"))

    user = User.query.get(user_id)

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("routes.home"))

    form = EditProfileForm(original_email=user.email, obj=user)

    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data

        if form.password.data:
            user.set_password(form.password.data)

        try:
            db.session.commit()
            flash(f"Profile updated for {user.name}!", "success")
            session["user_name"] = user.name
            session["user_email"] = user.email
            return redirect(url_for("routes.profile"))
        except Exception as e:
            db.session.rollback()
            flash(
                "An error occurred while updating the profile. Please try again.",
                "danger",
            )
            return redirect(url_for("routes.edit_profile"))

    return render_template("edit_profile.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            flash(f"Login successful for {user.name}!", "success")
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_email"] = user.email
            session["user_authenticated"] = True
            return redirect(url_for("routes.home"))
        else:
            flash("Login failed. Please check your email and password.", "danger")
    return render_template("login.html", form=form)

@bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Check if the email already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email address already registered. Please use a different email.', 'danger')
            # Render the form again with errors
            return render_template("register.html", form=form)

        # If not, create a new user
        new_user = User(
            name=form.name.data,
            email=form.email.data
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash(f"Registration successful for {form.name.data}! Please log in.", "success")
        return redirect(url_for("routes.login"))

    return render_template("register.html", form=form)


@bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form['password']
        if password == 'admin123':
            session['admin_logged_in'] = True
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin.index'))
        else:
            flash('Incorrect password. Please try again.', 'danger')
            return redirect(url_for('routes.admin_login'))
    return render_template('admin_login.html')

@bp.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('routes.admin_login'))

@bp.before_app_request
def restrict_admin_panel():
    # Ensure the endpoint exists before using .startswith()
    if request.endpoint and request.endpoint.startswith('admin.') and not session.get('admin_logged_in'):
        flash('You must log in as admin to access this page.', 'warning')
        return redirect(url_for('routes.admin_login'))


@bp.route("/add-service", methods=["GET", "POST"])
def add_service():
    form = BookingForm()
    if form.validate_on_submit():
        service_type = form.service_type.data
        availability = form.availability.data
        price = form.price.data

        if service_type.lower() == "flight":
            airline = form.airline.data or "Sample Airline"
            departure_city = form.departure_city.data or "Sample Departure"
            destination = form.destination.data or "Sample Destination"
            departure_time = form.departure_time.data or datetime.utcnow()
            return_date = form.return_date.data or datetime.utcnow()
            flight_number = form.flight_number.data or "FL123"

            service = Flight(
                availability=availability,
                price=price,
                airline=airline,
                departure_city=departure_city,
                destination=destination,
                departure_time=departure_time,
                arrival_time=return_date,
                flight_number=flight_number,
            )
        elif service_type.lower() == "hotel":
            hotel_name = form.hotel_name.data or "Sample Hotel"
            hotel_location = form.hotel_location.data or "Sample Location"
            hotel_rating = form.hotel_rating.data or 5
            checkin_date = form.checkin_date.data or datetime.utcnow()
            checkout_date = form.checkout_date.data or datetime.utcnow()

            service = Hotel(
                availability=availability,
                price=price,
                hotel_name=hotel_name,
                hotel_location=hotel_location,
                hotel_rating=hotel_rating,
                checkin_date=checkin_date,
                checkout_date=checkout_date,
            )
        else:
            flash('Invalid service type. Choose either "Flight" or "Hotel".', "danger")
            return redirect(url_for("routes.add_service"))

        db.session.add(service)
        db.session.commit()
        flash(f"{service_type.capitalize()} service added successfully!", "success")
        return redirect(url_for("routes.add_service"))

    return render_template("booking.html", form=form)

@bp.route('/edit_booking/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def update_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    form = UpdateBookingForm(obj=booking)

    if form.validate_on_submit():
        new_num_people = form.num_people.data
        delta = new_num_people - booking.num_people

        try:
            # Initialize flag to track availability
            availability_ok = True

            # Check availability based on service_type
            if booking.service_type == 'Flight' and booking.flight:
                if delta > 0:
                    if booking.flight.availability < delta:
                        flash(f"Not enough availability for the selected flight. Available: {booking.flight.availability}", "danger")
                        availability_ok = False

            elif booking.service_type == 'Hotel' and booking.hotel:
                if delta > 0:
                    if booking.hotel.availability < delta:
                        flash(f"Not enough availability for the selected hotel. Available: {booking.hotel.availability}", "danger")
                        availability_ok = False

            elif booking.service_type == 'PackageDeal' and booking.package_deal:
                if delta > 0:
                    if booking.package_deal.availability < delta:
                        flash(f"Not enough availability for the selected package deal. Available: {booking.package_deal.availability}", "danger")
                        availability_ok = False

            else:
                flash("Invalid service type or missing service details.", "danger")
                availability_ok = False

            if not availability_ok:
                return redirect(url_for('routes.profile'))

            # Adjust availability based on delta
            if booking.service_type == 'Flight' and booking.flight:
                if delta > 0:
                    booking.flight.availability -= delta
                elif delta < 0:
                    booking.flight.availability += abs(delta)

            elif booking.service_type == 'Hotel' and booking.hotel:
                if delta > 0:
                    booking.hotel.availability -= delta
                elif delta < 0:
                    booking.hotel.availability += abs(delta)

            elif booking.service_type == 'PackageDeal' and booking.package_deal:
                if delta > 0:
                    booking.package_deal.flight.availability -= delta
                    booking.package_deal.hotel.availability -= delta
                elif delta < 0:
                    booking.package_deal.flight.availability += abs(delta)
                    booking.package_deal.hotel.availability += abs(delta)

            # Update num_people and total_price
            booking.num_people = new_num_people
            booking.total_price = booking.calculate_total_price()

            db.session.commit()
            flash("Booking updated successfully.", "success")
            
           

            return redirect(url_for('routes.profile'))

        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"IntegrityError while updating booking ID {booking_id}: {e}")
            flash("An error occurred while updating your booking. Please try again.", "danger")
            return redirect(url_for('routes.profile'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Exception while updating booking ID {booking_id}: {e}")
            flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('routes.profile'))

    return render_template('edit_booking.html', form=form, booking=booking)

@bp.route("/create_package_deal/<int:flight_id>/<int:hotel_id>", methods=["POST"])
@login_required
def create_package_deal(flight_id, hotel_id):
    user_id = session.get("user_id")
    user = User.query.get(user_id)

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("routes.home"))

    start_date_str = request.form.get("start_date")
    end_date_str = request.form.get("end_date")

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid date format.", "danger")
        return redirect(url_for("routes.search"))

    flight = Flight.query.get_or_404(flight_id)
    hotel = Hotel.query.get_or_404(hotel_id)

    builder = PackageDealBuilder()
    try:
        package_deal = (
            builder.set_flight(flight)
            .set_hotel(hotel)
            .set_dates(start_date, end_date)
            .calculate_price()
            .build()
        )

        db.session.add(package_deal)
        db.session.commit()
        flash("Package deal created successfully!", "success")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating package deal: {e}")
        flash("Failed to create package deal. Please try again.", "danger")
        return redirect(url_for("routes.search"))

    booking = Booking(
        name=user.name,
        email=user.email,
        destination=flight.destination,
        booking_date=start_date.strftime("%Y-%m-%d"),
        num_people=session.get("num_people", 1),
        user_id=user.id,
        service_type="PackageDeal",
        flight_id=flight.id,
        hotel_id=hotel.id,
        package_deal_id=package_deal.id,
        total_price=package_deal.calculate_cost() * session.get("num_people", 1),
        flight_number=flight.flight_number,
    )
    db.session.add(booking)
    db.session.commit()

    flash("Package deal booked successfully!", "success")
    return redirect(url_for("routes.profile"))


@bp.route("/cancel-booking/<int:booking_id>", methods=["GET", "POST"])
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.is_confirmed:
        if booking.service_type == "Hotel" and booking.hotel:
            booking.hotel.availability += booking.num_people
        elif booking.service_type == "Flight" and booking.flight:
            booking.flight.availability += booking.num_people
        elif booking.service_type == "PackageDeal" and booking.package_deal:
            booking.hotel.availability += booking.num_people
            booking.flight.availability += booking.num_people

        booking.is_confirmed = False
        db.session.commit()
        flash("Booking has been canceled.", "success")
    else:
        flash("Booking is already canceled.", "info")

    return redirect(url_for("routes.profile"))


@bp.route("/search", methods=["GET", "POST"])
def search():
    """Simple travel search flow for flights, hotels and package deals."""
    if request.method == "POST":
        booking_type = request.form.get("booking_type")

        # First click selects the service and displays its search form.
        if booking_type in ["Flight", "Hotel", "PackageDeal"] and not request.form.get("destination"):
            return render_template("search.html", booking_type=booking_type)

        if booking_type not in ["Flight", "Hotel", "PackageDeal"]:
            flash("Please select Flight, Hotel or Package Deal.", "danger")
            return redirect(url_for("routes.search"))

        destination = (request.form.get("destination") or "").strip()
        guests_raw = request.form.get("guests", "1")
        try:
            guests = int(guests_raw)
            if guests < 1:
                raise ValueError
        except ValueError:
            flash("Number of guests/passengers must be at least 1.", "danger")
            return redirect(url_for("routes.search"))

        if not destination:
            flash("Destination is required.", "danger")
            return redirect(url_for("routes.search"))

        session["num_people"] = guests
        session["destination"] = destination

        results = []
        departure_city = None
        departure_time = None
        return_date = request.form.get("return_date")
        check_in = request.form.get("check_in")
        check_out = request.form.get("check_out")
        price_range = request.form.get("price_range")

        if booking_type == "Flight":
            departure_city = (request.form.get("departure_city") or "").strip()
            departure_time = request.form.get("departure_time")
            if not departure_city or not departure_time:
                flash("Departure city and departure date are required.", "danger")
                return redirect(url_for("routes.search"))
            try:
                dep_date = datetime.strptime(departure_time, "%Y-%m-%d")
                session["departure_time"] = departure_time
                session["booking_date"] = departure_time
            except ValueError:
                flash("Invalid departure date.", "danger")
                return redirect(url_for("routes.search"))

            if return_date:
                try:
                    if datetime.strptime(return_date, "%Y-%m-%d") < dep_date:
                        flash("Return date cannot be before departure date.", "danger")
                        return redirect(url_for("routes.search"))
                    session["return_date"] = return_date
                except ValueError:
                    flash("Invalid return date.", "danger")
                    return redirect(url_for("routes.search"))

            results = Flight.query.filter(
                Flight.destination.ilike(f"%{destination}%"),
                Flight.departure_city.ilike(f"%{departure_city}%"),
                Flight.availability >= guests,
            ).order_by(Flight.price.asc()).all()

        elif booking_type == "Hotel":
            if not check_in or not check_out:
                flash("Check-in and check-out dates are required.", "danger")
                return redirect(url_for("routes.search"))
            try:
                ci = datetime.strptime(check_in, "%Y-%m-%d")
                co = datetime.strptime(check_out, "%Y-%m-%d")
                if co <= ci:
                    raise ValueError
                session["check_in"] = check_in
                session["check_out"] = check_out
                session["booking_date"] = check_in
            except ValueError:
                flash("Check-out date must be after check-in date.", "danger")
                return redirect(url_for("routes.search"))

            results = Hotel.query.filter(
                Hotel.hotel_location.ilike(f"%{destination}%"),
                Hotel.availability >= guests,
            ).order_by(Hotel.price.asc()).all()

        else:
            if not check_in or not check_out:
                flash("Start and end dates are required for packages.", "danger")
                return redirect(url_for("routes.search"))
            try:
                ci = datetime.strptime(check_in, "%Y-%m-%d").date()
                co = datetime.strptime(check_out, "%Y-%m-%d").date()
                if co <= ci:
                    raise ValueError
                session["check_in"] = check_in
                session["check_out"] = check_out
                session["booking_date"] = check_in
            except ValueError:
                flash("End date must be after start date.", "danger")
                return redirect(url_for("routes.search"))

            results = PackageDeal.query.join(Flight, PackageDeal.flight_id == Flight.id).filter(
                Flight.destination.ilike(f"%{destination}%"),
                Flight.availability >= guests,
                Hotel.availability >= guests,
            ).order_by(PackageDeal.price.asc()).all()

            if price_range:
                try:
                    lo, hi = [float(x.strip()) for x in price_range.split("-", 1)]
                    results = [r for r in results if lo <= r.price <= hi]
                except ValueError:
                    flash("Price range must look like 5000-15000.", "danger")
                    return redirect(url_for("routes.search"))

        if not results:
            flash(f"No {booking_type} results found for {destination}. Try another destination or date.", "warning")

        return render_template(
            "search.html",
            booking_type=booking_type,
            destination=destination,
            check_in=check_in,
            check_out=check_out,
            departure_city=departure_city,
            departure_time=departure_time,
            return_date=return_date,
            guests=guests,
            price_range=price_range,
            results=results,
            currency="INR ",
        )

    return render_template("search.html")


@bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)  
    session.pop('user_authenticated', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('routes.home'))


@bp.route("/book/<string:booking_type>/<int:item_id>", methods=["POST"])
def book(booking_type, item_id):
    user_id = session.get("user_id")
    user_name = session.get("user_name")
    booking_email = session.get("user_email")
    session["booking_date_str"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    booking_date_str = session.get("booking_date_str")
    destination = session.get("destination")
    num_people = session.get("num_people")

    # Convert num_people to integer
    try:
        num_people = int(num_people)
        if num_people <= 0:
            raise ValueError
    except (TypeError, ValueError):
        flash("Please enter a valid number of passengers.", "danger")
        return redirect(url_for("routes.search"))

    # Validate booking_type
    if booking_type not in ["Flight", "Hotel", "PackageDeal"]:
        flash("Invalid booking type.", "danger")
        return redirect(url_for("routes.search"))

    # Validate required fields
    if not booking_email:
        flash("User email not found. Please log in again.", "danger")
        return redirect(url_for("routes.login"))
    if not destination:
        flash("Destination not found. Please perform a search first.", "danger")
        return redirect(url_for("routes.search"))
    if not booking_date_str:
        flash("Booking date not found. Please perform a search first.", "danger")
        return redirect(url_for("routes.search"))

    # Check if user is logged in
    if not user_id:
        flash("You must be logged in to make a booking.", "danger")
        return redirect(url_for("routes.login"))

    booking = None
    total_price = 0

    # Start operation logging and timing within the context
    with BookingContext(booking_type):
        try:
            if booking_type == "Flight":
                # Handle flight bookings
                flight = Flight.query.get(item_id)
                if not flight:
                    flash("Flight not found.", "danger")
                    return redirect(url_for("routes.search"))
                if flight.availability < num_people:
                    flash("Flight not available for the number of passengers.", "danger")
                    return redirect(url_for("routes.search"))

                # Update availability
                flight.availability -= num_people

                # Calculate total price
                flight_cost = flight.calculate_cost()
                if flight_cost is None:
                    flash("Failed to calculate flight cost.", "danger")
                    return redirect(url_for("routes.search"))
                total_price = flight_cost * num_people

                # Ensure flight_number exists
                flight_number = getattr(flight, "flight_number", None)
                if not flight_number:
                    flash("Flight number not found.", "danger")
                    return redirect(url_for("routes.search"))

                # Create booking
                booking = Booking(
                    user_id=user_id,
                    name=user_name,
                    email=booking_email,
                    destination=destination,
                    num_people=num_people,
                    service_type="Flight",
                    flight_id=flight.id,
                    hotel_id=None,
                    package_deal_id=None,
                    total_price=total_price,
                    flight_number=flight_number,
                )

            elif booking_type == "Hotel":
                # Handle hotel bookings
                hotel = Hotel.query.get(item_id)
                if not hotel:
                    flash("Hotel not found.", "danger")
                    return redirect(url_for("routes.search"))
                if hotel.availability < num_people:
                    flash("Hotel not available for the number of guests.", "danger")
                    return redirect(url_for("routes.search"))

                # Update availability
                hotel.availability -= num_people

                # Calculate total price
                hotel_cost = hotel.calculate_cost()
                if hotel_cost is None:
                    flash("Failed to calculate hotel cost.", "danger")
                    return redirect(url_for("routes.search"))
                total_price = hotel_cost * num_people

                # Create booking
                booking = Booking(
                    user_id=user_id,
                    name=user_name,
                    email=booking_email,
                    destination=destination,
                    num_people=num_people,
                    service_type="Hotel",
                    flight_id=None,
                    hotel_id=hotel.id,
                    package_deal_id=None,
                    total_price=total_price,
                    flight_number=None,
                )

            elif booking_type == "PackageDeal":
                # Handle package bookings
                package = PackageDeal.query.get(item_id)
                if not package:
                    flash("Package deal not found.", "danger")
                    return redirect(url_for("routes.search"))

                flight = package.flight
                hotel = package.hotel

                if not flight or not hotel:
                    flash("Package deal is incomplete. Please contact support.", "danger")
                    return redirect(url_for("routes.search"))

                if flight.availability < num_people or hotel.availability < num_people:
                    flash("Package deal not available for the number of guests.", "danger")
                    return redirect(url_for("routes.search"))

                # Update availability for both flight and hotel
                flight.availability -= num_people
                hotel.availability -= num_people

                # Calculate total price for the package
                package_cost = package.calculate_cost()
                if package_cost is None:
                    flash("Failed to calculate package cost.", "danger")
                    return redirect(url_for("routes.search"))
                total_price = package_cost * num_people

                # Ensure flight_number exists
                flight_number = getattr(flight, "flight_number", None)
                if not flight_number:
                    flash("Flight number not found in package deal.", "danger")
                    return redirect(url_for("routes.search"))

                # Create booking
                booking = Booking(
                    user_id=user_id,
                    name=user_name,
                    email=booking_email,
                    destination=destination,
                    num_people=num_people,
                    service_type="PackageDeal",
                    flight_id=flight.id,
                    hotel_id=hotel.id,
                    package_deal_id=package.id,
                    total_price=total_price,
                    flight_number=flight_number,
                )

            # Save the booking in the database
            db.session.add(booking)
            db.session.commit()

            # Store the last booking details in session
            session["last_booking"] = {
                "booking_type": booking_type,
                "item_id": item_id,
                "total_price": total_price,
                "service_type": booking.service_type,
            }
            flash(f"{booking_type} booking successful!", "success")
            return redirect(url_for("routes.profile"))

        except IntegrityError as e:
            db.session.rollback()
            flash(
                "An error occurred while processing your booking. Please try again.",
                "danger",
            )
            current_app.logger.error(f"IntegrityError during booking: {e}")
            return redirect(url_for("routes.search"))
        except Exception as e:
            db.session.rollback()  
            flash(f"An error occurred: {e}", "danger")
            current_app.logger.error(f"Error during booking: {e}")
            return redirect(url_for("routes.search"))


