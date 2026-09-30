import pytest

from app import create_app


@pytest.fixture()
def client(monkeypatch, tmp_path):
    db = tmp_path / "test.db"

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db}")
    monkeypatch.setenv("SECRET_KEY", "test-secret")

    app = create_app()
    app.config.update(TESTING=True)

    with app.test_client() as c:
        yield c


def register_user(client, name="Test User", email="testuser@example.com"):
    return client.post(
        "/register",
        data={
            "name": name,
            "email": email,
            "password": "Test@123",
            "confirm_password": "Test@123",
        },
        follow_redirects=True,
    )


# -------------------------------------------------
# BASIC APPLICATION TESTS
# -------------------------------------------------

def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "UP"


def test_metrics(client):
    response = client.get("/metrics")

    assert response.status_code == 200
    assert b"travel_booking_up 1" in response.data


def test_home(client):
    response = client.get("/")

    assert response.status_code == 200


# -------------------------------------------------
# REGISTRATION
# -------------------------------------------------

def test_register(client):
    response = register_user(client)

    assert response.status_code == 200


def test_register_invalid_email(client):
    response = client.post(
        "/register",
        data={
            "name": "Invalid User",
            "email": "invalid-email",
            "password": "Test@123",
            "confirm_password": "Test@123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200


def test_register_password_mismatch(client):
    response = client.post(
        "/register",
        data={
            "name": "Mismatch User",
            "email": "mismatch@example.com",
            "password": "Test@123",
            "confirm_password": "Wrong@123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200


# -------------------------------------------------
# LOGIN
# -------------------------------------------------

def test_login(client):
    register_user(
        client,
        name="Login User",
        email="loginuser@example.com",
    )

    response = client.post(
        "/login",
        data={
            "email": "loginuser@example.com",
            "password": "Test@123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200


def test_login_invalid_password(client):
    register_user(
        client,
        name="Wrong Password User",
        email="wrongpassword@example.com",
    )

    response = client.post(
        "/login",
        data={
            "email": "wrongpassword@example.com",
            "password": "WrongPassword@123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200


# -------------------------------------------------
# LOGOUT
# -------------------------------------------------

def test_logout(client):
    register_user(
        client,
        name="Logout User",
        email="logout@example.com",
    )

    client.post(
        "/login",
        data={
            "email": "logout@example.com",
            "password": "Test@123",
        },
        follow_redirects=True,
    )

    response = client.get("/logout", follow_redirects=True)

    assert response.status_code == 200


# -------------------------------------------------
# SEARCH PAGE
# -------------------------------------------------

def test_search_page(client):
    response = client.get("/search")

    assert response.status_code == 200


# -------------------------------------------------
# FLIGHT SEARCH VALIDATION
# -------------------------------------------------

def test_search_flight(client):
    response = client.post(
        "/search",
        data={
            "booking_type": "Flight",
            "destination": "Goa",
            "departure_city": "Mumbai",
            "departure_time": "2026-10-05",
            "return_date": "2026-10-07",
            "guests": "1",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200


# -------------------------------------------------
# HOTEL SEARCH VALIDATION
# -------------------------------------------------

def test_search_hotel(client):
    response = client.post(
        "/search",
        data={
            "booking_type": "Hotel",
            "destination": "Goa",
            "check_in": "2026-10-05",
            "check_out": "2026-10-07",
            "guests": "1",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200


# -------------------------------------------------
# PACKAGE SEARCH VALIDATION
# -------------------------------------------------

def test_search_package(client):
    response = client.post(
        "/search",
        data={
            "booking_type": "PackageDeal",
            "destination": "Goa",
            "check_in": "2026-10-05",
            "check_out": "2026-10-07",
            "guests": "1",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200


# -------------------------------------------------
# SEARCH VALIDATION - INVALID GUESTS
# -------------------------------------------------

def test_search_invalid_guests(client):
    response = client.post(
        "/search",
        data={
            "booking_type": "Flight",
            "destination": "Goa",
            "departure_city": "Mumbai",
            "departure_time": "2026-10-05",
            "return_date": "2026-10-07",
            "guests": "0",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200


# -------------------------------------------------
# SEARCH VALIDATION - INVALID DATE
# -------------------------------------------------

def test_search_invalid_flight_date(client):
    response = client.post(
        "/search",
        data={
            "booking_type": "Flight",
            "destination": "Goa",
            "departure_city": "Mumbai",
            "departure_time": "invalid-date",
            "return_date": "2026-10-07",
            "guests": "1",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200


# -------------------------------------------------
# SEARCH VALIDATION - RETURN DATE BEFORE DEPARTURE
# -------------------------------------------------

def test_search_return_date_before_departure(client):
    response = client.post(
        "/search",
        data={
            "booking_type": "Flight",
            "destination": "Goa",
            "departure_city": "Mumbai",
            "departure_time": "2026-10-10",
            "return_date": "2026-10-05",
            "guests": "1",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200


# -------------------------------------------------
# PROFILE WITHOUT LOGIN
# -------------------------------------------------

def test_profile_without_login(client):
    response = client.get("/profile", follow_redirects=True)

    assert response.status_code == 200


# -------------------------------------------------
# INVALID BOOKING TYPE
# -------------------------------------------------

def test_invalid_booking_type(client):
    response = client.post(
        "/book/InvalidType/999",
        follow_redirects=True,
    )

    assert response.status_code == 200