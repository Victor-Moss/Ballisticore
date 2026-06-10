"""Dashboard summary — key stats + recent issue/return activity."""
from datetime import datetime, time

from sqlalchemy.orm import Session

from app.models.firearm import Firearm
from app.models.guard import Guard
from app.models.permit import Permit
from app.models.register import Register
from app.models.register_history import RegisterHistory


def get_summary(db: Session) -> dict:
    total_firearms = db.query(Firearm).filter(Firearm.is_active == True).count()
    issued_firearms = db.query(Register).count()
    # Issued firearms are always active, so available = active inventory minus issued.
    available_firearms = max(total_firearms - issued_firearms, 0)
    active_guards = db.query(Guard).filter(Guard.is_active == True).count()
    total_permits = db.query(Permit).count()

    start_of_today = datetime.combine(datetime.utcnow().date(), time.min)
    permits_today = db.query(Permit).filter(Permit.issued_at >= start_of_today).count()

    history = (
        db.query(RegisterHistory)
        .filter(RegisterHistory.action.in_(["ISSUED", "RETURNED"]))
        .order_by(RegisterHistory.actioned_at.desc())
        .limit(10)
        .all()
    )

    recent_activity = []
    for h in history:
        guard = h.guard
        firearm = h.firearm
        firearm_label = ""
        if firearm:
            firearm_label = f"{firearm.make} {firearm.model or ''}".strip()
            if firearm.serial_number:
                firearm_label = f"{firearm_label} — {firearm.serial_number}".strip(" —")
        recent_activity.append({
            "id": h.id,
            "action": h.action,
            "at": h.actioned_at,
            "guard_name": f"{guard.first_name} {guard.last_name}" if guard else "Unknown guard",
            "firearm": firearm_label or "Unknown firearm",
        })

    return {
        "stats": {
            "total_firearms": total_firearms,
            "issued_firearms": issued_firearms,
            "available_firearms": available_firearms,
            "active_guards": active_guards,
            "total_permits": total_permits,
            "permits_today": permits_today,
        },
        "recent_activity": recent_activity,
    }
