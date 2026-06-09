import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class GuardFirearmPermission(Base):
    __tablename__ = "guard_firearm_permissions"
    __table_args__ = (UniqueConstraint("guard_id", "firearm_id", name="uq_guard_firearm"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    guard_id: Mapped[str] = mapped_column(String(36), ForeignKey("guards.id"), nullable=False)
    firearm_id: Mapped[str] = mapped_column(String(36), ForeignKey("firearms.id"), nullable=False)
    is_permitted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    guard: Mapped["Guard"] = relationship("Guard", back_populates="permissions")
    firearm: Mapped["Firearm"] = relationship("Firearm", back_populates="permissions")
