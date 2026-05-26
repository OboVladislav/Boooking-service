import pytest

from app.core.jwt import create_access_token


def test_not_empty_jwt():
    token = create_access_token({"user_id": 1, "role": "user"})

    assert token is not None