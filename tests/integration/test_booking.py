from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.booking_audit import BookingAuditLog
from app.models.room import Room


def _payload(room_id: int, *, hours_from_now: float = 2, duration_min: int = 60) -> dict:
    start = datetime.now(UTC) + timedelta(hours=hours_from_now)
    end = start + timedelta(minutes=duration_min)
    return {
        "room_id": room_id,
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
    }


class TestCreateBooking:
    def test_happy_path(self, client: TestClient, auth_headers, room: Room, db_session: Session):
        response = client.post("/bookings/", json=_payload(room.id), headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["room_id"] == room.id

        logs = db_session.query(BookingAuditLog).filter_by(action="created").all()
        assert len(logs) == 1

    def test_time_conflict(self, client: TestClient, auth_headers, room: Room):
        payload = _payload(room.id)
        assert client.post("/bookings/", json=payload, headers=auth_headers).status_code == 200
        second = client.post("/bookings/", json=payload, headers=auth_headers)
        assert second.status_code == 400

    def test_adjacent_slots_ok(self, client: TestClient, auth_headers, room: Room):
        start = datetime.now(UTC) + timedelta(hours=2)
        first = {
            "room_id": room.id,
            "start_time": start.isoformat(),
            "end_time": (start + timedelta(hours=1)).isoformat(),
        }
        second = {
            "room_id": room.id,
            "start_time": (start + timedelta(hours=1)).isoformat(),
            "end_time": (start + timedelta(hours=2)).isoformat(),
        }
        assert client.post("/bookings/", json=first, headers=auth_headers).status_code == 200
        assert client.post("/bookings/", json=second, headers=auth_headers).status_code == 200

    def test_room_not_found(self, client: TestClient, auth_headers):
        response = client.post("/bookings/", json=_payload(999999), headers=auth_headers)
        assert response.status_code == 404

    def test_no_auth(self, client: TestClient, room: Room):
        assert client.post("/bookings/", json=_payload(room.id)).status_code in (401, 403)

    @pytest.mark.parametrize("duration_min", [29, 600])  # <30мин и >8ч
    def test_invalid_duration(self, client, auth_headers, room, duration_min):
        payload = _payload(room.id, duration_min=duration_min)
        assert client.post("/bookings/", json=payload, headers=auth_headers).status_code == 400


class TestCancelBooking:
    def _create(self, client, headers, room, **kwargs) -> int:
        resp = client.post("/bookings/", json=_payload(room.id, **kwargs), headers=headers)
        assert resp.status_code == 200
        return resp.json()["id"]

    def test_owner_can_cancel(self, client, auth_headers, room):
        booking_id = self._create(client, auth_headers, room, hours_from_now=5)
        assert client.delete(f"/bookings/{booking_id}", headers=auth_headers).status_code == 200

    def test_cannot_cancel_within_deadline(self, client, auth_headers, room):
        # старт через 30 минут -> правило 1 часа не даст отменить
        booking_id = self._create(client, auth_headers, room, hours_from_now=0.5, duration_min=59)
        assert client.delete(f"/bookings/{booking_id}", headers=auth_headers).status_code == 400

    def test_admin_can_cancel_within_deadline(self, client, auth_headers, admin_headers, room):
        booking_id = self._create(client, auth_headers, room, hours_from_now=0.5, duration_min=60)
        assert client.delete(f"/bookings/{booking_id}", headers=admin_headers).status_code == 200

    def test_cancel_missing_404(self, client, auth_headers):
        assert client.delete("/bookings/999999", headers=auth_headers).status_code == 404


class TestBookingHistory:
    def test_history_records_actions(self, client, auth_headers, room):
        create = client.post("/bookings/", json=_payload(room.id, hours_from_now=5), headers=auth_headers)
        booking_id = create.json()["id"]
        client.patch(
            f"/bookings/{booking_id}",
            json={"start_time": (datetime.now(UTC) + timedelta(hours=6)).isoformat(),
                  "end_time": (datetime.now(UTC) + timedelta(hours=7)).isoformat()},
            headers=auth_headers,
        )
        client.delete(f"/bookings/{booking_id}", headers=auth_headers)

        response = client.get(f"/bookings/{booking_id}/history", headers=auth_headers)
        assert response.status_code == 200
        actions = [entry["action"] for entry in response.json()]
        assert "created" in actions
        assert "updated" in actions
        assert "cancelled" in actions