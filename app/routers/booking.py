import logging
from datetime import UTC

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.booking_rules import can_user_cancel, validate_booking_window
from app.core.db_safety import safe_commit, safe_flush
from app.dependencies.auth import get_current_user, get_db
from app.models.booking import Booking
from app.models.booking_audit import BookingAuditLog
from app.models.room import Room
from app.models.user import User
from app.schemas.audit import BookingAuditResponse
from app.schemas.booking import BookingCreate, BookingResponse, BookingUpdate

logger = logging.getLogger("booking-service.bookings")

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def write_audit_log(
        db: Session,
        booking_id: int,
        actor_user_id: int,
        action: str,
        payload: dict | None = None
):
    db.add(
        BookingAuditLog(
            booking_id=booking_id,
            actor_user_id=actor_user_id,
            action=action,
            payload=payload
        )
    )


@router.post("/", response_model=BookingResponse)
def create_booking(
        booking: BookingCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    start_utc, end_utc = validate_booking_window(booking.start_time, booking.end_time)

    room = db.query(Room).filter(Room.id == booking.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    overlapping_booking = db.query(Booking).filter(
        Booking.room_id == booking.room_id,
        and_(Booking.start_time < end_utc, Booking.end_time > start_utc)
    ).first()
    if overlapping_booking:
        raise HTTPException(status_code=400, detail="Room already booked in this time range")

    db_booking = Booking(
        room_id=booking.room_id,
        user_id=current_user.id,
        start_time=start_utc,
        end_time=end_utc
    )
    db.add(db_booking)
    safe_flush(db, logger, operation="create_booking")

    write_audit_log(
        db=db,
        booking_id=db_booking.id,
        actor_user_id=current_user.id,
        action="created",
        payload={
            "room_id": db_booking.room_id,
            "user_id": db_booking.user_id,
            "start_time": db_booking.start_time.isoformat(),
            "end_time": db_booking.end_time.isoformat()
        }
    )
    safe_commit(db, logger, operation="create_booking")
    db.refresh(db_booking)

    logger.info(
        "booking created booking_id=%s actor_user_id=%s room_id=%s",
        db_booking.id,
        current_user.id,
        db_booking.room_id
    )
    return db_booking


@router.patch("/{booking_id}", response_model=BookingResponse)
def update_booking(
        booking_id: int,
        payload: BookingUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    db_booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not db_booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    is_owner = db_booking.user_id == current_user.id
    is_admin = current_user.role == "admin"
    if not is_owner and not is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    old_state = {
        "room_id": db_booking.room_id,
        "start_time": db_booking.start_time.isoformat(),
        "end_time": db_booking.end_time.isoformat()
    }

    new_room_id = update_data.get("room_id", db_booking.room_id)
    new_start = update_data.get("start_time", db_booking.start_time)
    new_end = update_data.get("end_time", db_booking.end_time)
    start_utc, end_utc = validate_booking_window(new_start, new_end)

    room = db.query(Room).filter(Room.id == new_room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    overlapping_booking = db.query(Booking).filter(
        Booking.id != db_booking.id,
        Booking.room_id == new_room_id,
        and_(Booking.start_time < end_utc, Booking.end_time > start_utc)
    ).first()
    if overlapping_booking:
        raise HTTPException(status_code=400, detail="Room already booked in this time range")

    db_booking.room_id = new_room_id
    db_booking.start_time = start_utc
    db_booking.end_time = end_utc

    write_audit_log(
        db=db,
        booking_id=db_booking.id,
        actor_user_id=current_user.id,
        action="updated",
        payload={
            "before": old_state,
            "after": {
                "room_id": db_booking.room_id,
                "start_time": db_booking.start_time.isoformat(),
                "end_time": db_booking.end_time.isoformat()
            }
        }
    )
    safe_commit(db, logger, operation="update_booking")
    db.refresh(db_booking)

    logger.info("booking updated booking_id=%s actor_user_id=%s", db_booking.id, current_user.id)
    return db_booking


@router.delete("/{booking_id}")
def cancel_booking(
        booking_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    db_booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not db_booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    is_owner = db_booking.user_id == current_user.id
    is_admin = current_user.role == "admin"
    if not is_owner and not is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    booking_start = db_booking.start_time
    if booking_start.tzinfo is None:
        booking_start = booking_start.replace(tzinfo=UTC)
    if not is_admin and not can_user_cancel(booking_start):
        raise HTTPException(
            status_code=400,
            detail="Cancellation is unavailable less than 1 hour before start"
        )

    write_audit_log(
        db=db,
        booking_id=db_booking.id,
        actor_user_id=current_user.id,
        action="cancelled",
        payload={
            "room_id": db_booking.room_id,
            "user_id": db_booking.user_id,
            "start_time": db_booking.start_time.isoformat(),
            "end_time": db_booking.end_time.isoformat()
        }
    )
    db.delete(db_booking)
    safe_commit(db, logger, operation="cancel_booking")

    logger.info("booking cancelled booking_id=%s actor_user_id=%s", booking_id, current_user.id)
    return {"detail": "Booking cancelled"}


@router.get("/{booking_id}/history", response_model=list[BookingAuditResponse])
def get_booking_history(
        booking_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    is_admin = current_user.role == "admin"
    if booking and booking.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if not booking and not is_admin:
        raise HTTPException(status_code=403, detail="Only admin can view history for cancelled bookings")

    logs = db.query(BookingAuditLog).filter(
        BookingAuditLog.booking_id == booking_id
    ).order_by(BookingAuditLog.changed_at.asc()).all()
    if not logs:
        raise HTTPException(status_code=404, detail="Booking history not found")
    return logs


@router.get("/my", response_model=list[BookingResponse])
def get_my_bookings(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return db.query(Booking).filter(Booking.user_id == current_user.id).all()
