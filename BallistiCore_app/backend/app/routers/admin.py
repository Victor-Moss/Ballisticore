"""Administrative server controls (super admin only)."""
import os
import signal
import threading
import time

from fastapi import APIRouter, Depends

from app.core.auth import require_admin

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# Seconds to let the /shutdown response flush and any in-flight requests finish
# before we tear the process down, and how long to wait for a graceful uvicorn
# stop before forcing exit.
_GRACE_SECONDS = 1.5
_FORCE_SECONDS = 3.0


def _shutdown_process() -> None:
    """Stop the server from within the process.

    Runs in a background thread so the HTTP handler can return first. Gives a
    short grace period, asks uvicorn to shut down gracefully via SIGINT, and
    guarantees the process exits even if that signal isn't delivered (Windows
    delivery into the asyncio proactor loop is unreliable)."""
    time.sleep(_GRACE_SECONDS)
    try:
        # uvicorn installs a SIGINT handler that drains in-flight requests and
        # runs lifespan shutdown before exiting. Best-effort on Windows.
        signal.raise_signal(signal.SIGINT)
    except Exception:
        pass
    time.sleep(_FORCE_SECONDS)
    # Hard stop as a fallback so the button always works.
    os._exit(0)


@router.post("/shutdown")
def shutdown_server(current_user=Depends(require_admin)):
    """Gracefully stop the BallistiCore server. Super admin only.

    All sessions are invalidated implicitly: tokens are stamped with a per-process
    session epoch (see app.core.auth), so once the process restarts every prior
    token is rejected and users must sign in again."""
    threading.Thread(target=_shutdown_process, daemon=True).start()
    return {"detail": "Server is shutting down."}
