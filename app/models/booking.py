from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.room import Room
    from app.models.user import User


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    start_time: Mapped[datetime]
    end_time: Mapped[datetime]

    room: Mapped["Room"] = relationship(back_populates="bookings")
    user: Mapped["User"] = relationship(back_populates="bookings")
