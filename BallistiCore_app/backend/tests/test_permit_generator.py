"""
Permit PDF generation.

Covers the company-type rule for the guard's residential address: it prints on a
security company's permit and is suppressed on a CIT company's, where permits
travel with the route rather than the individual guard.

Text is read back out of the generated PDF rather than asserted against the table
data, so these tests fail if the row is dropped from the layout but still drawn.
"""
import base64
import re
import uuid
import zlib
from datetime import datetime

import pytest

from app.services import permit_generator as gen
from tests.conftest import make_user, make_guard, make_firearm


def pdf_text(path: str) -> str:
    """The drawn text of a PDF, as one string.

    ReportLab writes page content as ASCII85-then-Flate encoded streams, with
    each string drawn as a literal `(…) Tj`. Decode the streams and pull the
    literals out — no third-party PDF library needed.
    """
    raw = open(path, "rb").read()
    out = []
    for match in re.finditer(rb"stream\r?\n(.*?)endstream", raw, re.S):
        chunk = match.group(1)
        for decode in (lambda c: base64.a85decode(c, adobe=True), zlib.decompress):
            try:
                chunk = decode(chunk)
            except Exception:  # noqa: BLE001 — stream may use either/neither filter
                pass
        out.extend(m.group(1).decode("latin-1") for m in re.finditer(rb"\((.*?)\)\s*Tj", chunk, re.S))
    return "\n".join(out)


@pytest.fixture
def permit_setup(db, tmp_path, monkeypatch):
    """A guard with an address, plus the permit/firearm needed to render a PDF.

    PDFs are written to tmp_path so the real backend/permits directory is left
    alone.
    """
    monkeypatch.setattr(gen, "PERMITS_DIR", tmp_path)

    from app.models.permit import Permit
    guard = make_guard(db)
    guard.cell_phone = "0821234567"
    guard.physical_address = "12 Main Road, Springs"
    db.commit()

    firearm = make_firearm(db)
    permit = Permit(
        id=str(uuid.uuid4()),
        permit_number=f"BC-{uuid.uuid4().hex[:6]}",
        guard_id=guard.id,
        firearm_id=firearm.id,
        issued_by=make_user(db, username=f"iss-{uuid.uuid4().hex[:6]}").id,
        issued_at=datetime.utcnow(),
    )
    db.add(permit)
    db.commit()
    return permit, guard, firearm


def test_security_company_permit_shows_address(db, permit_setup, monkeypatch):
    monkeypatch.setattr(gen, "is_cit_company", lambda: False)
    permit, guard, firearm = permit_setup

    text = pdf_text(gen.generate_full_permit(db, permit, guard, firearm))

    assert "Address:" in text
    assert "12 Main Road, Springs" in text


def test_cit_company_permit_omits_address_and_its_label(db, permit_setup, monkeypatch):
    monkeypatch.setattr(gen, "is_cit_company", lambda: True)
    permit, guard, firearm = permit_setup

    text = pdf_text(gen.generate_full_permit(db, permit, guard, firearm))

    assert "12 Main Road, Springs" not in text
    # The label goes with the value — a bare "Address:" row would be a visible hole.
    assert "Address:" not in text


def test_cit_company_permit_keeps_the_rest_of_the_guard_block(db, permit_setup, monkeypatch):
    """Suppressing the address must not disturb the surrounding layout."""
    monkeypatch.setattr(gen, "is_cit_company", lambda: True)
    permit, guard, firearm = permit_setup

    text = pdf_text(gen.generate_full_permit(db, permit, guard, firearm))

    assert "Name:" in text
    assert f"{guard.first_name} {guard.last_name}" in text
    assert "ID Number:" in text
    assert "Cell Phone:" in text
    assert "0821234567" in text
    assert "Personnel No:" in text
    # Sections printed below the guard block are still intact.
    assert "Serial / Firearm No:" in text
    assert "Date Issued:" in text


def test_mini_permit_never_carried_the_address(db, permit_setup, monkeypatch):
    """The mini permit has no address row for either company type."""
    permit, guard, firearm = permit_setup

    monkeypatch.setattr(gen, "is_cit_company", lambda: False)
    security_text = pdf_text(gen.generate_mini_permit(db, permit, guard, firearm))
    monkeypatch.setattr(gen, "is_cit_company", lambda: True)
    cit_text = pdf_text(gen.generate_mini_permit(db, permit, guard, firearm))

    assert "12 Main Road, Springs" not in security_text
    assert "12 Main Road, Springs" not in cit_text
