import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.booking_rules import validate_booking_window
from app.core.db_safety import safe_commit
from app.dependencies.auth import get_db, require_admin
from app.models.booking import Booking
from app.models.room import Room
from app.schemas.booking import BookingResponse
from app.schemas.room import RoomCreate, RoomResponse

logger = logging.getLogger("booking-service.rooms")

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.post("/", response_model=RoomResponse)
def create_room(
        room: RoomCreate,
        db: Session = Depends(get_db),
        _admin=Depends(require_admin)
):
    db_room = Room(**room.model_dump())
    db.add(db_room)
    safe_commit(db, logger, operation="create_room")
    db.refresh(db_room)
    return db_room


@router.get("/", response_model=list[RoomResponse])
def get_rooms(capacity: int | None = None, location: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Room)
    if capacity is not None:
        query = query.filter(Room.capacity >= capacity)
    if location:
        query = query.filter(Room.location.ilike(f"%{location}%"))
    return query.all()


@router.get("/available", response_model=list[RoomResponse])
def get_available_rooms(
        start_time: datetime = Query(...),
        end_time: datetime = Query(...),
        capacity: int | None = Query(None),
        location: str | None = Query(None),
        db: Session = Depends(get_db)
):
    start_utc, end_utc = validate_booking_window(start_time, end_time)

    busy_room_subquery = db.query(Booking.room_id).filter(
        and_(Booking.start_time < end_utc, Booking.end_time > start_utc)
    )

    query = db.query(Room).filter(~Room.id.in_(busy_room_subquery))
    if capacity is not None:
        query = query.filter(Room.capacity >= capacity)
    if location:
        query = query.filter(Room.location.ilike(f"%{location}%"))
    return query.all()


@router.get("/{room_id}", response_model=RoomResponse)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.delete("/{room_id}")
def delete_room(
        room_id: int,
        db: Session = Depends(get_db),
        _admin=Depends(require_admin)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    db.delete(room)
    safe_commit(db, logger, operation="delete_room")
    return {"detail": "Room deleted"}


@router.get("/{room_id}/bookings", response_model=list[BookingResponse])
def get_room_bookings(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return db.query(Booking).filter(Booking.room_id == room_id).all()


@router.get("/{room_id}/availability")
def check_room_availability(
        room_id: int,
        start_time: datetime = Query(...),
        end_time: datetime = Query(...),
        db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    start_utc, end_utc = validate_booking_window(start_time, end_time)
    overlapping_booking = db.query(Booking).filter(
        Booking.room_id == room_id,
        and_(Booking.start_time < end_utc, Booking.end_time > start_utc)
    ).first()
    return {"available": overlapping_booking is None}
