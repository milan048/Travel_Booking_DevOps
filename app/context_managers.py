from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


@contextmanager
def BookingContext(booking_type):
    """
    context manager to handle booking process.
    Ensures that resources are properly managed during the booking.
    """
    # Initial setup for the booking session
    logger.info(f"Starting {booking_type} booking session...")
    try:
        yield  # Yield control back to the code within the 'with' block
        # If everything is successful, finalize the booking
        logger.info(f"{booking_type} booking completed successfully.")
    except Exception as e:
        # Handle any exceptions that occur during booking
        logger.error(f"Error during {booking_type} booking: {e}")
        # You could rollback or clean up if necessary
        raise
    finally:
        # Clean up logic goes here (e.g., unlocking resources, closing connections)
        logger.info(f"Cleaning up {booking_type} booking session.")
