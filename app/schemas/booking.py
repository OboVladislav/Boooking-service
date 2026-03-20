from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BookingCreate(BaseModel):
    room_id: int
    start_time: datetime
    end_time: datetime


class BookingUpdate(BaseModel):
    room_id: int | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    user_id: int
    start_time: datetime
    end_time: datetime
