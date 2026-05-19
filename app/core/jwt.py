from datetime import UTC, datetime, timedelta

from jose import jwt

from app.core.config import settings


def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    return encoded_jwt
