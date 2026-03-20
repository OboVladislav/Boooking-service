from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BookingAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    booking_id: int
    actor_user_id: int
    action: str
    payload: dict | None
    changed_at: datetime
