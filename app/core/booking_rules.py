from datetime import UTC, datetime, timedelta

from fastapi import HTTPException

MIN_BOOKING_DURATION = timedelta(minutes=30)
MAX_BOOKING_DURATION = timedelta(hours=8)
CANCELLATION_DEADLINE = timedelta(hours=1)


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise HTTPException(status_code=400, detail="Datetime must include timezone")
    return value.astimezone(UTC)


def validate_booking_window(start_time: datetime, end_time: datetime) -> tuple[datetime, datetime]:
    start_utc = normalize_datetime(start_time)
    end_utc = normalize_datetime(end_time)

    if start_utc >= end_utc:
        raise HTTPException(status_code=400, detail="start_time must be earlier than end_time")

    now = datetime.now(UTC)
    if start_utc <= now:
        raise HTTPException(status_code=400, detail="start_time must be in the future")

    duration = end_utc - start_utc
    if duration < MIN_BOOKING_DURATION:
        raise HTTPException(status_code=400, detail="Booking is too short")
    if duration > MAX_BOOKING_DURATION:
        raise HTTPException(status_code=400, detail="Booking is too long")

    return start_utc, end_utc


def can_user_cancel(start_time: datetime, now: datetime | None = None) -> bool:
    current_time = now or datetime.now(UTC)
    start_utc = normalize_datetime(start_time)
    return start_utc - current_time >= CANCELLATION_DEADLINE
