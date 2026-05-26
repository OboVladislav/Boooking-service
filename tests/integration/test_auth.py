from starlette.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User

class TestRegister:
    def test_register_new_user(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={"email": "bob@example.com", "password": "secret123"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["email"] == "bob@example.com"
        assert "password" not in body
        assert "password_hash" not in body

    def test_first_user_is_admin(self, client: TestClient, db_session: Session):
        client.post("auth/register", json={"email": "first@example.com", "password": "x12345"})
        created = db_session.query(User).filter(User.email == "first@example.com").first()

        assert created.role == "admin"


    def test_second_user_is_not_admin(self, client: TestClient, db_session: Session):
        client.post("auth/register", json={"email": "first@example.com", "password": "x12345"})
        client.post("auth/register", json={"email": "second@example.com", "password": "x12345"})
        created = db_session.query(User).filter(User.email == "second@example.com").first()

        assert created.role == "user"

    def test_duplicated_email(self, client: TestClient, user: User):
        response = client.post("auth/register", json={"email": user.email, "password": user.password_hash})

        assert response.status_code == 400

class TestLogin:
    def test_login_success(self, client: TestClient, user: User):
        response = client.post("auth/login", json={"email": user.email, "password": "password123"})

        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_failure_email(self, client: TestClient):
        response = client.post(
            "auth/login",
            json={"email": "who@who.who", "password": "secret123"},
        )

        assert response.status_code == 401

    def test_login_failure_password(self, client: TestClient, user: User):
        response = client.post(
            "/auth/login",
            json={"email": user.email , "password": "whatever1"},
        )

        assert response.status_code == 401