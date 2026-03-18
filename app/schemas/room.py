from pydantic import BaseModel


class RoomCreate(BaseModel):
    name: str
    capacity: int
    location: str


class RoomResponse(BaseModel):
    id: int
    name: str
    capacity: int
    location: str

    class Config:
        orm_mode = True