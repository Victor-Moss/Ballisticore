import uuid
from typing import Optional
from datetime import datetime, date
from sqlalchemy import String, Boolean, Text, DateTime, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Firearm(Base):
    __tablename__ = "firearms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    serial_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    make: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    calibre: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    license_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    license_issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ammunition_type_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("ammunition_types.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    ammunition_type: Mapped[Optional["AmmunitionType"]] = relationship("AmmunitionType", back_populates="firearms")
    permissions: Mapped[list["GuardFirearmPermission"]] = relationship("GuardFirearmPermission", back_populates="firearm")
    register_entry: Mapped[Optional["Register"]] = relationship("Register", back_populates="firearm", uselist=False)
    history_entries: Mapped[list["RegisterHistory"]] = relationship("RegisterHistory", back_populates="firearm")
    permits: Mapped[list["Permit"]] = relationship("Permit", back_populates="firearm")

    @property
    def ammunition_type_name(self) -> Optional[str]:
        return self.ammunition_type.name if self.ammunition_type else None
