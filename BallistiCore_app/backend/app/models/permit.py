import uuid
from typing import Optional
from datetime import datetime, date, time
from sqlalchemy import String, Boolean, Integer, DateTime, Date, Time, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Permit(Base):
    __tablename__ = "permits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    permit_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    guard_id: Mapped[str] = mapped_column(String(36), ForeignKey("guards.id"), nullable=False)
    firearm_id: Mapped[str] = mapped_column(String(36), ForeignKey("firearms.id"), nullable=False)
    issued_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    valid_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    whatsapp_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    whatsapp_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    pdf_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Issuance details
    rounds_issued: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ammunition_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    period_from_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    valid_until_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    cit_cell_route: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    witness: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    saps_competency_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Return inspection fields
    rounds_returned: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    firearm_returned_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    in_order: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    posted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Electronic signature — guard authenticated with their password at issue.
    # This is the "Received by" signature on the permit (guard receiving the firearm).
    guard_signed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    guard_signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    guard_signature_method: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # Issuing staff member's electronic signature at issue — the "Issued by"
    # signature. The operator re-enters their account password to sign.
    issuer_signed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    issuer_signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Return signatures, captured when the firearm is handed back.
    #   return_guard_*    — the guard returning the firearm ("Returned by")
    #   return_received_* — the staff member receiving the return ("Received by")
    return_guard_signed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    return_guard_signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    return_received_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    return_received_signed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    return_received_signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    guard: Mapped["Guard"] = relationship("Guard", back_populates="permits")
    firearm: Mapped["Firearm"] = relationship("Firearm", back_populates="permits")
    issued_by_user: Mapped["User"] = relationship("User", foreign_keys=[issued_by])
    return_received_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[return_received_by])
