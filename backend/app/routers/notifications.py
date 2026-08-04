from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import PendingNotification, User
from ..schemas import NotificationOut
from ..security import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return (
        db.query(PendingNotification)
        .filter_by(user_id=user.id, read_at=None)
        .order_by(PendingNotification.air_date)
        .all()
    )


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    notification = (
        db.query(PendingNotification)
        .filter_by(id=notification_id, user_id=user.id)
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.read_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(notification)
    return notification
