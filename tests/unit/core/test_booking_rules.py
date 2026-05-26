import pytest
from fastapi import HTTPException
from datetime import datetime, UTC, timedelta, timezone


from app.core.booking_rules import (
    CANCELLATION_DEADLINE,
    MAX_BOOKING_DURATION,
    MIN_BOOKING_DURATION,
    can_user_cancel,
    normalize_datetime,
    validate_booking_window,
)


def future(hours: float) -> datetime:
    return datetime.now(UTC) + timedelta(hours=hours)

class TestNormalizeDatetime:
    def test_naive_datetime_raises(self):
        with pytest.raises(HTTPException) as e:
            normalize_datetime(datetime(2026, 5, 21, 12, 0))
            assert e.value.status_code == 400
            assert "timezone" in e.value.detail.lower()

    def test_aware_datetime_returns_utc(self):
        # +3 часа смещение -> должно стать UTC
        moscow = timezone(timedelta(hours=3))
        value = datetime(2026, 5, 21, 15, 0, tzinfo=moscow)
        result = normalize_datetime(value)
        assert result.tzinfo == UTC
        assert result.hour == 12  # 15:00 +03:00 == 12:00 UTC

    def test_utc_datetime_unchanged(self):
        value = datetime(2026, 5, 21, 12, 0, tzinfo=UTC)
        result = normalize_datetime(value)
        assert result == value


class TestValidateBookingWindow:
    def test_valid_window_returns_utc(self):
        start = future(2.0)
        end = start + timedelta(hours=1)
        res_start, res_end = validate_booking_window(start, end)
        assert res_start.tzinfo == UTC
        assert res_end.tzinfo == UTC
        assert res_end > res_start

    def test_valid_window_equal_raises(self):
        start = future(2.0)
        with pytest.raises(HTTPException) as e:
            res_start, res_end = validate_booking_window(start, start)
        assert e.value.status_code == 400
        assert "earlier" in e.value.detail.lower()

    def test_calid_window_start_before_end(self):
        start = future(3.0)
        end = future(3.0)
        with pytest.raises(HTTPException) as e:
            res_start, res_end = validate_booking_window(start, end)
        assert e.value.status_code == 400
        # assert "earlier" in e.value.detail.lower()

    def test_start_in_past_raises(self):
        start = datetime.now(UTC) - timedelta(hours=1)
        end = start + timedelta(hours=1)
        with pytest.raises(HTTPException) as exc:
            validate_booking_window(start, end)
        assert "future" in exc.value.detail.lower()

    def test_duration_below_minimum_raises(self):
        start = future(2)
        end = start + MIN_BOOKING_DURATION - timedelta(minutes=1)  # 29 минут
        with pytest.raises(HTTPException) as exc:
            validate_booking_window(start, end)
        assert "short" in exc.value.detail.lower()

    def test_duration_exactly_minimum_is_ok(self):
        start = future(2)
        end = start + MIN_BOOKING_DURATION  # ровно 30 минут — граница
        result_start, result_end = validate_booking_window(start, end)
        assert result_end - result_start == MIN_BOOKING_DURATION

    def test_duration_above_maximum_raises(self):
        start = future(2)
        end = start + MAX_BOOKING_DURATION + timedelta(minutes=1)
        with pytest.raises(HTTPException) as exc:
            validate_booking_window(start, end)
        assert "long" in exc.value.detail.lower()

    def test_duration_exactly_maximum_is_ok(self):
        start = future(2)
        end = start + MAX_BOOKING_DURATION  # ровно 8 часов — граница
        result_start, result_end = validate_booking_window(start, end)
        assert result_end - result_start == MAX_BOOKING_DURATION

    def test_naive_input_raises(self):
        start = datetime(2099, 1, 1, 12, 0)  # naive
        end = datetime(2099, 1, 1, 13, 0)
        with pytest.raises(HTTPException) as exc:
            validate_booking_window(start, end)
        assert "timezone" in exc.value.detail.lower()

class TestCanUserCancel:
    def test_user_can_cancel_success(self):
        start = future(2.0)
        assert can_user_cancel(start) is True

    def test_user_cancel_exactly_at_deadline(self):
        start = datetime.now(UTC)
        end = start + CANCELLATION_DEADLINE
        assert can_user_cancel(start, end) is False

    def test_inside_deadline_returns_false(self):
        now = datetime.now(UTC)
        start = now + timedelta(minutes=30)
        assert can_user_cancel(start, now=now) is False

    def test_past_start_returns_false(self):
        now = datetime.now(UTC)
        start = now - timedelta(hours=1)
        assert can_user_cancel(start, now=now) is False

    def test_naive_start_raises(self):
        now = datetime(2026, 5, 21, 12, 0, tzinfo=UTC)
        start = datetime(2026, 5, 21, 14, 0)  # naive
        with pytest.raises(HTTPException):
            can_user_cancel(start, now=now)
    