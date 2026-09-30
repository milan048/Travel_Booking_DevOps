from datetime import date
from app.models import PackageDeal, Flight, Hotel
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  


class PackageDealBuilder:
    def __init__(self):
        self._flight = None
        self._hotel = None
        self._start_date = None
        self._end_date = None
        self._price = None

    def set_flight(self, flight: Flight):
        if not isinstance(flight, Flight):
            raise TypeError("Expected a Flight instance.")
        self._flight = flight
        logger.debug(f"PackageDealBuilder: Set flight to {flight}")
        return self

    def set_hotel(self, hotel: Hotel):
        if not isinstance(hotel, Hotel):
            raise TypeError("Expected a Hotel instance.")
        self._hotel = hotel
        logger.debug(f"PackageDealBuilder: Set hotel to {hotel}")
        return self

    def set_dates(self, start_date: date, end_date: date):
        if not isinstance(start_date, date) or not isinstance(end_date, date):
            raise TypeError("start_date and end_date must be date instances.")
        if end_date < start_date:
            raise ValueError("end_date cannot be before start_date.")
        self._start_date = start_date
        self._end_date = end_date
        logger.debug(f"PackageDealBuilder: Set dates from {start_date} to {end_date}")
        return self

    def calculate_price(self):
        if not self._flight or not self._hotel:
            raise ValueError("Flight and Hotel must be set before calculating price.")
        self._price = self._flight.calculate_cost() + self._hotel.calculate_cost()
        logger.debug(f"PackageDealBuilder: Calculated price {self._price}")
        return self

    def build(self):
        if (
            not self._flight
            or not self._hotel
            or not self._start_date
            or not self._end_date
            or self._price is None
        ):
            raise ValueError(
                "Flight, Hotel, start_date, end_date, and price must be set before building."
            )
        package_deal = PackageDeal(
            flight_id=self._flight.id,
            hotel_id=self._hotel.id,
            start_date=self._start_date,
            end_date=self._end_date,
            price=self._price,
        )
        logger.debug(f"PackageDealBuilder: Built PackageDeal {package_deal}")
        return package_deal
