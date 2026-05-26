from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.booking import Booking


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str]
    role: Mapped[str] = mapped_column(default="user", server_default="user")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")
