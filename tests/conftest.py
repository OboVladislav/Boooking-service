from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import hash_password
from app.database import Base
from app.dependencies.dep import get_db
from app.main import app
from app.models.room import Room
from app.models.user import User

TEST_DATABASE_URL = "postgresql://postgres:root@localhost:5433/booking_test"


# start db before all tests
@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

# get session do trans + rollback
@pytest.fixture
def db_session(engine) -> Iterator[Session]:

    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

#test user
@pytest.fixture
def user(db_session: Session) -> User:
    user = User(
        email="alice@example.com",
        password_hash=hash_password("password123"),
        role="user",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

# test admin
@pytest.fixture
def admin(db_session: Session) -> User:
    admin = User(
        email="admin@example.com",
        password_hash=hash_password("admin123"),
        role="admin",
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

# get token for user
@pytest.fixture
def user_token(client: TestClient, user: User) -> str:

    response = client.post(
        "/auth/login",
        json={"email": user.email, "password": "password123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(user_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_token}"}

# get token for admin
@pytest.fixture
def admin_token(client: TestClient, admin: User) -> str:
    response = client.post(
        "/auth/login",
        json={"email": admin.email, "password": "admin123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def admin_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture
def room(db_session: Session) -> Room:
    room = Room(name="Aurora", capacity=10, location="Floor 2")
    db_session.add(room)
    db_session.commit()
    db_session.refresh(room)
    return room