import uuid
from typing import Optional
from datetime import datetime, date
from sqlalchemy import String, Boolean, Text, DateTime, Date, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Guard(Base):
    __tablename__ = "guards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    id_number: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    psira_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    cell_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # Telegram Chat ID — the delivery address when the messaging provider is
    # Telegram. The guard must send /start to the company bot first to obtain it.
    telegram_chat_id: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    physical_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("locations.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Extra profile fields
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    personnel_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # SAPS competency per weapon type
    saps_comp_carbine: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    saps_expiry_carbine: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    saps_comp_handgun: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    saps_expiry_handgun: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    saps_comp_rifle: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    saps_expiry_rifle: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    saps_comp_shotgun: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    saps_expiry_shotgun: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Weapon-type clearance flags
    permitted_carbine: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    permitted_handgun: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    permitted_rifle: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    permitted_shotgun: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Sign-in account — lets the guard electronically sign for firearms.
    # Separate from operator `users`: a guard login can ONLY sign, never run the system.
    username: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    password_set_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_signin_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Self-service password reset via WhatsApp OTP (single active reset at a time).
    reset_otp_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reset_otp_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reset_otp_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    location: Mapped[Optional["Location"]] = relationship("Location", back_populates="guards")
    permissions: Mapped[list["GuardFirearmPermission"]] = relationship("GuardFirearmPermission", back_populates="guard")
    register_entries: Mapped[list["Register"]] = relationship("Register", back_populates="guard")
    history_entries: Mapped[list["RegisterHistory"]] = relationship("RegisterHistory", back_populates="guard")
    permits: Mapped[list["Permit"]] = relationship("Permit", back_populates="guard")
    cit_routes: Mapped[list["GuardCITRoute"]] = relationship("GuardCITRoute", back_populates="guard", cascade="all, delete-orphan")


class GuardCITRoute(Base):
    __tablename__ = "guard_cit_routes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    guard_id: Mapped[str] = mapped_column(String(36), ForeignKey("guards.id"), nullable=False)
    route_name: Mapped[str] = mapped_column(String(100), nullable=False)
    cell_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    guard: Mapped["Guard"] = relationship("Guard", back_populates="cit_routes")
