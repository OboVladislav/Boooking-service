from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String

from app.database import Base


class BookingAuditLog(Base):
    __tablename__ = "booking_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, index=True, nullable=False)
    actor_user_id = Column(Integer, index=True, nullable=False)
    action = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    changed_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
