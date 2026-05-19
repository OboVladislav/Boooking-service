from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.booking import Booking


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(unique=True, index=True)
    capacity: Mapped[int | None]
    location: Mapped[str | None]

    bookings: Mapped[list["Booking"]] = relationship(back_populates="room")
