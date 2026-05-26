import logging

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session


def safe_flush(db: Session, logger: logging.Logger, operation: str):
    try:
        db.flush()
    except IntegrityError as e:
        db.rollback()
        logger.warning("integrity error during flush operation=%s", operation)
        raise HTTPException(status_code=409, detail="Data integrity violation") from e
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("database error during flush operation=%s", operation)
        raise HTTPException(status_code=500, detail="Database operation failed") from e


def safe_commit(db: Session, logger: logging.Logger, operation: str):
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.warning("integrity error during commit operation=%s", operation)
        raise HTTPException(status_code=409, detail="Data integrity violation") from e
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("database error during commit operation=%s", operation)
        raise HTTPException(status_code=500, detail="Database operation failed") from e
