from pydantic import BaseModel
from datetime import datetime


class BookingCreate(BaseModel):
    room_id: int
    start_time: datetime
    end_time: datetime


class BookingUpdate(BaseModel):
    room_id: int | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


class BookingResponse(BaseModel):
    id: int
    room_id: int
    user_id: int
    start_time: datetime
    end_time: datetime

    class Config:
        orm_mode = True
