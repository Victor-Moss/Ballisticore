import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class RegisterHistory(Base):
    __tablename__ = "register_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    guard_id: Mapped[str] = mapped_column(String(36), ForeignKey("guards.id"), nullable=False)
    firearm_id: Mapped[str] = mapped_column(String(36), ForeignKey("firearms.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # 'ISSUED' or 'RETURNED'
    actioned_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    actioned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Ammunition tracking
    ammunition_issued: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ammunition_returned: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ammunition_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Inspection flags
    firearm_inspected_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    firearm_returned_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    permit_returned: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Signatures (file paths)
    guard_signature: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    authorising_officer_signature: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    audit_signature: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Electronic signature — guard authenticated at the time of this action
    guard_signed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    guard_signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # CIT / responsible person
    cit_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    responsible_person_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    guard: Mapped["Guard"] = relationship("Guard", back_populates="history_entries")
    firearm: Mapped["Firearm"] = relationship("Firearm", back_populates="history_entries")
    actioned_by_user: Mapped["User"] = relationship("User", foreign_keys=[actioned_by])
