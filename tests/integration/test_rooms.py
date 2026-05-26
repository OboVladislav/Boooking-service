import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.room import Room


class TestCreateRoom:
    def test_admin_can_create(self, client: TestClient, admin_headers):
        response = client.post(
            "/rooms/",
            json={"name": "Nova", "capacity": 5, "location": "Floor 1"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Nova"

    def test_regular_user_forbidden(self, client: TestClient, auth_headers):
        response = client.post(
            "/rooms/",
            json={"name": "Nova", "capacity": 5, "location": "Floor 1"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_no_token_unauthorized(self, client: TestClient):
        response = client.post("/rooms/", json={"name": "X", "capacity": 1, "location": "Y"})
        assert response.status_code in (401, 403)


class TestListRooms:
    def test_lists_existing(self, client: TestClient, room: Room):
        response = client.get("/rooms/")
        assert response.status_code == 200
        names = [r["name"] for r in response.json()]
        assert "Aurora" in names

    def test_capacity_filter(self, client: TestClient, db_session: Session):
        db_session.add_all([
            Room(name="Small", capacity=2, location="A"),
            Room(name="Big", capacity=20, location="A"),
        ])
        db_session.commit()
        response = client.get("/rooms/", params={"capacity": 10})
        names = [r["name"] for r in response.json()]
        assert "Big" in names
        assert "Small" not in names

    def test_location_filter_partial(self, client: TestClient, db_session: Session):
        db_session.add_all([
            Room(name="R1", capacity=5, location="Floor 2 North"),
            Room(name="R2", capacity=5, location="Basement"),
        ])
        db_session.commit()
        response = client.get("/rooms/", params={"location": "floor 2"})
        names = [r["name"] for r in response.json()]
        assert "R1" in names
        assert "R2" not in names


class TestGetDeleteRoom:
    def test_get_existing(self, client: TestClient, room: Room):
        response = client.get(f"/rooms/{room.id}")
        assert response.status_code == 200

    def test_get_missing_404(self, client: TestClient):
        assert client.get("/rooms/999999").status_code == 404

    def test_admin_deletes(self, client: TestClient, admin_headers, room: Room):
        response = client.delete(f"/rooms/{room.id}", headers=admin_headers)
        assert response.status_code == 200

    def test_user_cannot_delete(self, client: TestClient, auth_headers, room: Room):
        assert client.delete(f"/rooms/{room.id}", headers=auth_headers).status_code == 403

    def test_delete_missing_404(self, client: TestClient, admin_headers):
        assert client.delete("/rooms/999999", headers=admin_headers).status_code == 404