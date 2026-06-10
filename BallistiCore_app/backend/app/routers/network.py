"""Network info — lets the UI show how to reach this server from other devices."""
import socket

from fastapi import APIRouter, Depends

from app.core.auth import require_active_user

router = APIRouter(prefix="/api/network", tags=["Network"], dependencies=[Depends(require_active_user)])


def _detect_lan_ip() -> str:
    """Best-effort primary LAN IPv4 of this machine.

    Opens a UDP socket toward a public address (no packets are actually sent)
    so the OS picks the interface it would use to reach the network, then reads
    that interface's address. Falls back to the hostname lookup.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return ""
    finally:
        s.close()


@router.get("/info")
def network_info():
    """Return this server's LAN address so the UI can show a shareable URL."""
    return {"lan_ip": _detect_lan_ip(), "hostname": socket.gethostname()}
