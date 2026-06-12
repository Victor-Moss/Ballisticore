from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.core.config import settings
from app.core.branding import branding
from app.core import license as lic
from app.core.database import SessionLocal
from app.routers import auth, locations, ammunition_types, guards, firearms, permissions, register, permits, reports, guard_self, network, imports, dashboard, branding as branding_router, license as license_router
from app.services.users import seed_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        admin = seed_admin(db)
        print(f"Admin user ready — id: {admin.id}")
    finally:
        db.close()
    status = lic.reload()
    print(f"License: state={status.state} read_only={status.read_only} "
          f"company={status.company!r} expires={status.expires_at}")
    yield


# Requests that are allowed even when the license is in read-only mode. Only
# authentication — operators must still be able to sign in to view records.
_LICENSE_ALLOWLIST = {"/api/auth/login"}
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

app = FastAPI(
    title=f"{branding['app_name']} API",
    description="Firearms Register Management System",
    version="1.0.0",
    lifespan=lifespan,
)


# Read-only enforcement. When the license is expired/missing/invalid, every
# state-changing request (POST/PUT/PATCH/DELETE) is rejected, so the app becomes
# read-only across the board without having to remember each mutating route.
# Registered BEFORE CORS so CORSMiddleware stays outermost and still tags the
# 403 with CORS headers. GETs always pass — viewing records is never blocked.
@app.middleware("http")
async def license_read_only(request: Request, call_next):
    if request.method not in _SAFE_METHODS and request.url.path not in _LICENSE_ALLOWLIST:
        status = lic.get_status()
        if status.read_only:
            return JSONResponse({"detail": status.message}, status_code=403)
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(license_router.router)
app.include_router(branding_router.router)
app.include_router(auth.router)
app.include_router(locations.router)
app.include_router(ammunition_types.router)
app.include_router(guards.router)
app.include_router(guard_self.router)
app.include_router(firearms.router)
app.include_router(permissions.router)
app.include_router(register.router)
app.include_router(permits.router)
app.include_router(permits.public_router)
app.include_router(reports.router)
app.include_router(network.router)
app.include_router(imports.router)
app.include_router(dashboard.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "system": branding["app_name"], "environment": settings.ENVIRONMENT}


# ── Serve the built React frontend (self-hosted single-process mode) ──────────
# When FRONTEND_DIST points at a Vite `dist/` build, the backend serves the UI
# itself: hashed assets under /assets, and every other non-API path falls back to
# index.html so client-side (React Router) deep links work on refresh. Left blank
# in development, where Vite serves the UI on :5173 and this block is skipped.
if settings.FRONTEND_DIST.strip():
    _frontend_dist = Path(settings.FRONTEND_DIST.strip())
else:
    # Default: BallistiCore_app/frontend/dist relative to this file (dev convenience).
    _frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"

if (_frontend_dist / "index.html").is_file():
    _assets_dir = _frontend_dist / "assets"
    if _assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="assets")

    # API/docs paths that must keep returning JSON (not the SPA shell) when unmatched.
    _RESERVED = ("api/", "api", "health", "docs", "redoc", "openapi.json")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if any(full_path == p or full_path.startswith(p) for p in _RESERVED):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        candidate = _frontend_dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(_frontend_dist / "index.html"))
