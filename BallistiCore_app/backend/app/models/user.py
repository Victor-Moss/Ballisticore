import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Extra profile fields
    personnel_number: Mapped[str] = mapped_column(String(20), nullable=True)
    psira_number: Mapped[str] = mapped_column(String(20), nullable=True)
    competency: Mapped[str] = mapped_column(String(100), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    id_number: Mapped[str] = mapped_column(String(20), nullable=True)

    # Granular permissions
    perm_new_permits: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    perm_return_permits: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    perm_manage_weapons: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    perm_manage_staff: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    perm_access_database: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    perm_send_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    perm_view_register_history: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    perm_system_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    perm_add_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    perm_modify_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    perm_change_passwords: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    perm_clear_logs: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Weapon-category permissions
    perm_carbine: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    perm_handgun: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    perm_rifle: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    perm_shotgun: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
