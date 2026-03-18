from datetime import datetime

from pydantic import BaseModel


class BookingAuditResponse(BaseModel):
    id: int
    booking_id: int
    actor_user_id: int
    action: str
    payload: dict | None
    changed_at: datetime

    class Config:
        orm_mode = True
