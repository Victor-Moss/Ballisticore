"""
Bulk import from the BallistiCore Excel template.

Provides:
  - build_template()  -> bytes  : the blank .xlsx (Guards / Firearms / Users)
  - import_workbook(db, data)    : parse + validate + insert, returning a
                                   per-sheet report of imported / failed / skipped rows.

Validation is per-row: a bad row is reported with its sheet, row number and
reason, and never blocks the valid rows in the same upload.
"""
from io import BytesIO

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.comments import Comment
from openpyxl.utils import get_column_letter
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.schemas.firearm import FirearmCreate, FIREARM_TYPES
from app.schemas.guard import GuardCreate
from app.services import firearms as firearm_svc
from app.services import guards as guard_svc
from app.services import users as user_svc

# Rows whose first cell starts with this are treated as format examples and skipped.
EXAMPLE_PREFIX = "e.g."

_HEADER_FILL = PatternFill("solid", fgColor="1D4ED8")
_HEADER_FONT = Font(bold=True, color="FFFFFF")
_EXAMPLE_FONT = Font(italic=True, color="64748B")


def _cell_str(v) -> str:
    """Normalise a cell value to a trimmed string ('' for blanks)."""
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def _truthy(v: str) -> bool:
    return _cell_str(v).lower() in {"yes", "y", "true", "1", "x", "admin"}


# ── Creators: validate one row's values and insert. Raise on any problem. ─────
def _create_guard(db: Session, v: dict):
    data = GuardCreate(
        first_name=v["first_name"], last_name=v["last_name"],
        id_number=v.get("id_number") or None,
        psira_number=v.get("psira_number") or None,
        cell_phone=v.get("cell_phone") or None,
        email=v.get("email") or None,
        physical_address=v.get("physical_address") or None,
        personnel_number=v.get("personnel_number") or None,
    )
    guard_svc.create(db, data)


def _create_firearm(db: Session, v: dict):
    ftype = (v.get("type") or "").lower()
    if ftype and ftype not in FIREARM_TYPES:
        raise ValueError(f"Type must be one of: {', '.join(FIREARM_TYPES)}")
    if firearm_svc.get_by_serial(db, v["serial_number"]):
        raise ValueError(f"A firearm with serial '{v['serial_number']}' already exists")
    data = FirearmCreate(
        serial_number=v["serial_number"], make=v["make"],
        model=v.get("model") or None, type=ftype or None,
        calibre=v.get("calibre") or None,
        license_number=v.get("license_number") or None,
        description=v.get("description") or None,
    )
    firearm_svc.create(db, data)


def _create_user(db: Session, v: dict):
    if len(v.get("password", "")) < 6:
        raise ValueError("Password must be at least 6 characters")
    if user_svc.get_by_username(db, v["username"]):
        raise ValueError(f"Username '{v['username']}' already exists")
    user_svc.create(
        db, username=v["username"], email=v.get("email") or None,
        password=v["password"], is_admin=_truthy(v.get("is_admin", "")),
        personnel_number=v.get("personnel_number") or None,
        psira_number=v.get("psira_number") or None,
        phone_number=v.get("phone_number") or None,
        id_number=v.get("id_number") or None,
    )


# ── Sheet definitions ─────────────────────────────────────────────────────────
# Each column: (header, field, required, example, comment)
SHEETS = [
    {
        "name": "Guards",
        "creator": _create_guard,
        "columns": [
            ("First Name *",       "first_name",       True,  "e.g. John",                None),
            ("Last Name *",        "last_name",        True,  "Smith",                    None),
            ("ID Number",          "id_number",        False, "8001015009087",            None),
            ("PSIRA Number",       "psira_number",     False, "PS1234567",                None),
            ("Cell Phone",         "cell_phone",       False, "0821234567",               None),
            ("Email",              "email",            False, "john.smith@example.com",   None),
            ("Physical Address",   "physical_address", False, "12 Main Rd, Springs",      None),
            ("Personnel Number",   "personnel_number", False, "EMP-001",                  None),
        ],
    },
    {
        "name": "Firearms",
        "creator": _create_firearm,
        "columns": [
            ("Serial Number *",    "serial_number",  True,  "e.g. GLK-100234", None),
            ("Make *",             "make",           True,  "Glock",           None),
            ("Model",              "model",          False, "17",              None),
            ("Type",               "type",           False, "handgun",         "One of: carbine, handgun, rifle, shotgun (or leave blank)"),
            ("Calibre",            "calibre",        False, "9mm",             None),
            ("Licence Number",     "license_number", False, "LIC-2024-001",    None),
            ("Description",        "description",    False, "Duty pistol",     None),
        ],
    },
    {
        "name": "Users",
        "creator": _create_user,
        "columns": [
            ("Username *",         "username",         True,  "e.g. joperator",          None),
            ("Password *",         "password",         True,  "ChangeMe!23",             "At least 6 characters"),
            ("Email",              "email",            False, "joperator@example.com",   None),
            ("Is Admin",           "is_admin",         False, "no",                      "yes = full administrator, no = operator"),
            ("Personnel Number",   "personnel_number", False, "EMP-100",                 None),
            ("PSIRA Number",       "psira_number",     False, "PS9988776",               None),
            ("Phone Number",       "phone_number",     False, "0837654321",              None),
            ("ID Number",          "id_number",        False, "9002025009088",           None),
        ],
    },
]


# ── Template generation ───────────────────────────────────────────────────────
def build_template() -> bytes:
    wb = Workbook()
    wb.remove(wb.active)  # drop the default sheet
    for sheet in SHEETS:
        ws = wb.create_sheet(title=sheet["name"])
        cols = sheet["columns"]
        # Header row
        for c, (header, _field, _req, _ex, comment) in enumerate(cols, start=1):
            cell = ws.cell(row=1, column=c, value=header)
            cell.fill = _HEADER_FILL
            cell.font = _HEADER_FONT
            cell.alignment = Alignment(horizontal="left", vertical="center")
            if comment:
                cell.comment = Comment(comment, "BallistiCore")
            ws.column_dimensions[get_column_letter(c)].width = max(16, len(header) + 4)
        # Example row (ignored on import — first cell starts with "e.g.")
        for c, (_h, _f, _r, example, _cm) in enumerate(cols, start=1):
            cell = ws.cell(row=2, column=c, value=example)
            cell.font = _EXAMPLE_FONT
        ws.freeze_panes = "A2"
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ── Import ────────────────────────────────────────────────────────────────────
def _friendly_error(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        parts = []
        for e in exc.errors():
            loc = ".".join(str(x) for x in e.get("loc", ())) or "value"
            parts.append(f"{loc}: {e.get('msg', 'invalid')}")
        return "; ".join(parts)
    if isinstance(exc, IntegrityError):
        return "Duplicate or invalid value (rejected by a database constraint)"
    return str(exc) or exc.__class__.__name__


def import_workbook(db: Session, data: bytes) -> dict:
    try:
        wb = load_workbook(BytesIO(data), data_only=True, read_only=True)
    except Exception:
        raise ValueError("That file is not a valid .xlsx workbook.")

    results = []
    total_imported = total_failed = 0

    for sheet in SHEETS:
        name = sheet["name"]
        cols = sheet["columns"]
        imported = 0
        skipped = 0
        errors = []

        if name not in wb.sheetnames:
            results.append({"sheet": name, "imported": 0, "failed": 0,
                            "skipped": 0, "errors": [],
                            "note": "Sheet not found in the uploaded file."})
            continue

        ws = wb[name]
        # Map by header text so column order in the file doesn't matter.
        header_cells = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), ())
        header_to_field = {}
        for header, field, *_ in cols:
            for idx, hc in enumerate(header_cells):
                if _cell_str(hc).lower() == header.lower():
                    header_to_field[field] = idx
                    break

        for excel_row, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            values = {field: _cell_str(row[idx]) if idx < len(row) else ""
                      for field, idx in header_to_field.items()}
            if not any(values.values()):
                continue  # fully blank row
            first = next(iter(values.values()), "")
            if first.lower().startswith(EXAMPLE_PREFIX):
                skipped += 1
                continue
            missing = [h for (h, f, req, *_ ) in cols if req and not values.get(f)]
            if missing:
                errors.append({"row": excel_row, "message": f"Missing required: {', '.join(missing)}"})
                continue
            try:
                sheet["creator"](db, values)
                imported += 1
            except Exception as exc:  # noqa: BLE001 — per-row isolation is intentional
                db.rollback()
                errors.append({"row": excel_row, "message": _friendly_error(exc)})

        total_imported += imported
        total_failed += len(errors)
        results.append({"sheet": name, "imported": imported,
                        "failed": len(errors), "skipped": skipped, "errors": errors})

    wb.close()
    return {"imported": total_imported, "failed": total_failed, "sheets": results}
