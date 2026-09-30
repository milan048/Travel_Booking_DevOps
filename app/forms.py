from flask_wtf import FlaskForm
from wtforms import (
    FloatField,
    SelectField,
    StringField,
    PasswordField,
    SubmitField,
    IntegerField,
    DateField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    NumberRange,
    Optional,
    EqualTo,
    ValidationError,
)
from app.models import Flight, Hotel, User


class RegistrationForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Invalid email address."),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required."),
            Length(min=6, message="Password must be at least 6 characters long."),
        ],
    )
    submit = SubmitField("Login")


class BookingForm(FlaskForm):
    service_type = SelectField(
        "Service Type",
        choices=[("Flight", "Flight"), ("Hotel", "Hotel")],
        validators=[DataRequired()],
    )
    # Fields for Flight
    airline = StringField("Airline")
    departure_city = StringField("Departure City")
    destination = StringField("Destination")
    departure_date = DateField("Departure Date", format="%Y-%m-%d")
    return_date = DateField("Return Date", format="%Y-%m-%d")
    flight_number = StringField("Flight Number")
    passengers = IntegerField("Number of Passengers", validators=[NumberRange(min=1)])

    # Fields for Hotel
    hotel_name = StringField("Hotel Name")
    location = StringField("Location")
    hotel_rating = IntegerField("Hotel Rating", validators=[NumberRange(min=1, max=5)])
    checkin_date = DateField("Check-in Date", format="%Y-%m-%d")
    checkout_date = DateField("Check-out Date", format="%Y-%m-%d")

    availability = IntegerField("Availability", validators=[DataRequired()])
    price = FloatField("Price", validators=[DataRequired()])
    submit = SubmitField("Add Service")


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    subject = StringField("Subject", validators=[DataRequired()])
    message = TextAreaField("Message", validators=[DataRequired()])
    submit = SubmitField("Send Message")


class PackageDealForm(FlaskForm):
    flight_id = SelectField(
        "Flight", choices=[], coerce=int, validators=[DataRequired()]
    )
    hotel_id = SelectField("Hotel", choices=[], coerce=int, validators=[DataRequired()])
    start_date = DateField("Start Date", format="%Y-%m-%d", validators=[DataRequired()])
    end_date = DateField("End Date", format="%Y-%m-%d", validators=[DataRequired()])
    price = FloatField(
        "Price",
        validators=[
            DataRequired(),
            NumberRange(min=0.0, message="Price must be a positive number."),
        ],
    )
    submit = SubmitField("Create Package Deal")

    def __init__(self, *args, **kwargs):
        super(PackageDealForm, self).__init__(*args, **kwargs)
        self.flight_id.choices = [
            (flight.id, flight.airline) for flight in Flight.query.all()
        ]
        self.hotel_id.choices = [
            (hotel.id, hotel.hotel_name) for hotel in Hotel.query.all()
        ]


class UpdateBookingForm(FlaskForm):
    num_people = IntegerField(
        "Number of People",
        validators=[
            DataRequired(),
            NumberRange(min=1, message="Number of people must be at least 1."),
        ],
    )
    submit = SubmitField("Update Booking")


class EditProfileForm(FlaskForm):
    name = StringField(
        "Full Name", validators=[DataRequired(message="Name is required.")]
    )
    email = StringField(
        "Email Address",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Invalid email address."),
        ],
    )
    password = PasswordField(
        "Password (Optional)",
        validators=[
            Optional(),
            Length(min=6, message="Password must be at least 6 characters long."),
        ],
    )
    submit = SubmitField("Update Profile")

    def __init__(self, original_email, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_email = original_email

    def validate_email(self, field):
        if field.data != self.original_email:
            if User.query.filter_by(email=field.data).first():
                raise ValidationError(
                    "This email is already in use. Please choose a different one."
                )
