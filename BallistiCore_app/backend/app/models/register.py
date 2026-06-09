import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Register(Base):
    __tablename__ = "register"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    guard_id: Mapped[str] = mapped_column(String(36), ForeignKey("guards.id"), nullable=False)
    firearm_id: Mapped[str] = mapped_column(String(36), ForeignKey("firearms.id"), unique=True, nullable=False)
    issued_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    permit_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("permits.id"), nullable=True)

    # Issuance detail snapshot
    ammunition_issued: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ammunition_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    firearm_inspected_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    cit_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    responsible_person_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Electronic signature — guard acknowledged receipt with their password
    guard_signed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    guard_signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    guard: Mapped["Guard"] = relationship("Guard", back_populates="register_entries")
    firearm: Mapped["Firearm"] = relationship("Firearm", back_populates="register_entry")
    issued_by_user: Mapped["User"] = relationship("User", foreign_keys=[issued_by])
    permit: Mapped[Optional["Permit"]] = relationship("Permit", foreign_keys=[permit_id])
