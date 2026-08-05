from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import require_active_user
from app.core.messaging_config import (
    PROVIDERS,
    get_messaging,
    get_provider,
    save_messaging,
)
from app.routers.auth import require_admin
from app.services import messaging_service

router = APIRouter(prefix="/api/messaging", tags=["Messaging"])


class MessagingConfig(BaseModel):
    provider: str
    telegram_bot_token: Optional[str] = ""
    whatsapp_account_sid: Optional[str] = ""
    whatsapp_auth_token: Optional[str] = ""
    whatsapp_from_number: Optional[str] = ""


class MessagingTestRequest(MessagingConfig):
    recipient: Optional[str] = None


def _validate_provider(provider: str) -> None:
    if provider not in PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Provider must be one of: {', '.join(PROVIDERS)}",
        )


def _validate_credentials(cfg: MessagingConfig) -> None:
    """Reject a save that selects a provider without its required credentials."""
    if cfg.provider == "telegram" and not (cfg.telegram_bot_token or "").strip():
        raise HTTPException(status_code=400, detail="A Telegram bot token is required.")
    if cfg.provider == "whatsapp":
        missing = [
            label
            for label, val in (
                ("Account SID", cfg.whatsapp_account_sid),
                ("Auth Token", cfg.whatsapp_auth_token),
                ("From Number", cfg.whatsapp_from_number),
            )
            if not (val or "").strip()
        ]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"WhatsApp requires: {', '.join(missing)}.",
            )


@router.get("/provider")
def get_messaging_provider(current_user=Depends(require_active_user)):
    """Active provider only (no credentials) — lets guard forms and the import
    template show the right delivery field. Available to any signed-in user."""
    return {"provider": get_provider()}


@router.get("/")
def get_messaging_config(current_user=Depends(require_admin)):
    """Admin only — full messaging config for the settings form."""
    return dict(get_messaging())


@router.put("/")
def update_messaging_config(cfg: MessagingConfig, current_user=Depends(require_admin)):
    """Admin only — re-validate credentials, then persist to config.json."""
    _validate_provider(cfg.provider)
    _validate_credentials(cfg)
    save_messaging(cfg.model_dump())
    return dict(get_messaging())


@router.post("/test")
def test_messaging(req: MessagingTestRequest, current_user=Depends(require_admin)):
    """Admin only — send a test message with the supplied (unsaved) credentials."""
    _validate_provider(req.provider)
    ok, message = messaging_service.send_test_message(
        provider=req.provider,
        credentials=req.model_dump(),
        recipient=req.recipient or "",
    )
    return {"ok": ok, "message": message}
