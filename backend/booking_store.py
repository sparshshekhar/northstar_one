from typing import Dict
from models import SiteVisitBooking, BookingResponse

# Simulated fully-booked slots — deterministic, for reproducible test cases
UNAVAILABLE_SLOTS = {
    ("2026-08-25", "11:00 AM"),
    ("2026-08-26", "05:00 PM"),
}

# Track bookings per session, so analytics (Step 5) can read the outcome
_bookings: Dict[str, BookingResponse] = {}


def attempt_booking(req: SiteVisitBooking) -> BookingResponse:
    slot = (req.preferred_date, req.preferred_time)

    if slot in UNAVAILABLE_SLOTS:
        result = BookingResponse(
            session_id=req.session_id,
            status="failed",
            message=(
                f"That slot on {req.preferred_date} at {req.preferred_time} is "
                "already booked. Would a different time work, or should I have "
                "someone call you to reschedule?"
            ),
            alternate_suggestion="Same day, 2 hours later" if req.preferred_time != "05:00 PM" else None,
        )
    else:
        result = BookingResponse(
            session_id=req.session_id,
            status="confirmed",
            message=(
                f"Your site visit for the {req.configuration} is confirmed on "
                f"{req.preferred_date} at {req.preferred_time}. We'll call "
                f"{req.contact_number} to confirm."
            ),
        )

    _bookings[req.session_id] = result
    return result


def get_booking(session_id: str) -> BookingResponse | None:
    return _bookings.get(session_id)