"""
Unit tests — Issuance engine (services/issuance.py)
All tests run against in-memory SQLite — no real DB touched.
"""
import pytest
from fastapi import HTTPException
from tests.conftest import make_user, make_guard, make_firearm, make_permission
from app.services import issuance as svc


def _issue(db, guard, firearm, user):
    """Helper: issue a firearm and return the register entry."""
    return svc.issue_firearm(db, guard.id, firearm.id, user.id)


class TestPermitNumberGeneration:
    def test_format(self):
        num = svc._generate_permit_number.__wrapped__(1) if hasattr(svc._generate_permit_number, '__wrapped__') else None
        # Call directly — function takes a sequence number
        from datetime import date
        today = date.today().strftime("%Y%m%d")
        # Can't call _generate_permit_number directly (it queries DB),
        # so verify the prefix pattern via a full issue instead.

    def test_permit_number_via_issue(self, db):
        user = make_user(db)
        guard = make_guard(db)
        firearm = make_firearm(db)
        make_permission(db, guard.id, firearm.id)
        entry = _issue(db, guard, firearm, user)
        assert entry.permit is not None or entry.permit_id is not None
        # Retrieve the permit
        from app.models.permit import Permit
        permit = db.query(Permit).first()
        assert permit is not None
        from app.core.branding import branding
        assert permit.permit_number.startswith(branding["permit_prefix"] + "-")
        parts = permit.permit_number.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 8   # YYYYMMDD
        assert parts[2].isdigit()


class TestIssuanceValidation:
    def test_inactive_guard_blocked(self, db):
        user = make_user(db)
        guard = make_guard(db, is_active=False)
        firearm = make_firearm(db)
        make_permission(db, guard.id, firearm.id)
        with pytest.raises(HTTPException) as exc:
            _issue(db, guard, firearm, user)
        assert exc.value.status_code in (400, 404)

    def test_inactive_firearm_blocked(self, db):
        user = make_user(db)
        guard = make_guard(db)
        firearm = make_firearm(db, is_active=False)
        make_permission(db, guard.id, firearm.id)
        with pytest.raises(HTTPException) as exc:
            _issue(db, guard, firearm, user)
        assert exc.value.status_code in (400, 404)

    def test_no_permission_blocked(self, db):
        user = make_user(db)
        guard = make_guard(db)
        firearm = make_firearm(db)
        # Deliberately no make_permission call
        with pytest.raises(HTTPException) as exc:
            _issue(db, guard, firearm, user)
        assert exc.value.status_code == 403

    def test_successful_issue_creates_register_entry(self, db):
        user = make_user(db)
        guard = make_guard(db)
        firearm = make_firearm(db)
        make_permission(db, guard.id, firearm.id)
        entry = _issue(db, guard, firearm, user)
        assert entry.guard_id == guard.id
        assert entry.firearm_id == firearm.id
        assert entry.issued_by == user.id

    def test_successful_issue_creates_history_entry(self, db):
        user = make_user(db)
        guard = make_guard(db)
        firearm = make_firearm(db)
        make_permission(db, guard.id, firearm.id)
        _issue(db, guard, firearm, user)
        from app.models.register_history import RegisterHistory
        history = db.query(RegisterHistory).all()
        assert len(history) == 1
        assert history[0].action.lower() == "issued"
        assert history[0].guard_id == guard.id

    def test_successful_issue_creates_permit(self, db):
        user = make_user(db)
        guard = make_guard(db)
        firearm = make_firearm(db)
        make_permission(db, guard.id, firearm.id)
        _issue(db, guard, firearm, user)
        from app.models.permit import Permit
        permits = db.query(Permit).all()
        assert len(permits) == 1
        assert permits[0].guard_id == guard.id
        assert permits[0].firearm_id == firearm.id


class TestDoubleBookingPrevention:
    def test_double_booking_blocked(self, db):
        user = make_user(db)
        guard1 = make_guard(db, first_name="Guard", last_name="One", id_number="1111111111111")
        guard2 = make_guard(db, first_name="Guard", last_name="Two", id_number="2222222222222")
        firearm = make_firearm(db)
        make_permission(db, guard1.id, firearm.id)
        make_permission(db, guard2.id, firearm.id)

        # Issue to guard1
        _issue(db, guard1, firearm, user)

        # Attempt to issue same firearm to guard2 — must be blocked
        with pytest.raises(HTTPException) as exc:
            _issue(db, guard2, firearm, user)
        assert exc.value.status_code == 409

    def test_double_booking_error_names_current_holder(self, db):
        user = make_user(db)
        guard1 = make_guard(db, first_name="Jane", last_name="Doe", id_number="1111111111111")
        guard2 = make_guard(db, first_name="Jim", last_name="Beam", id_number="2222222222222")
        firearm = make_firearm(db)
        make_permission(db, guard1.id, firearm.id)
        make_permission(db, guard2.id, firearm.id)

        _issue(db, guard1, firearm, user)

        with pytest.raises(HTTPException) as exc:
            _issue(db, guard2, firearm, user)
        # Error message should mention the current holder
        assert "Jane" in exc.value.detail or "Doe" in exc.value.detail

    def test_same_guard_cannot_double_carry(self, db):
        user = make_user(db)
        guard = make_guard(db)
        firearm = make_firearm(db)
        make_permission(db, guard.id, firearm.id)
        _issue(db, guard, firearm, user)
        with pytest.raises(HTTPException) as exc:
            _issue(db, guard, firearm, user)
        assert exc.value.status_code == 409

    def test_different_firearms_can_both_be_issued(self, db):
        """Two guards, two different firearms — both should succeed."""
        user = make_user(db)
        guard1 = make_guard(db, first_name="A", last_name="A", id_number="1111111111111")
        guard2 = make_guard(db, first_name="B", last_name="B", id_number="2222222222222")
        fa1 = make_firearm(db, serial_number="GUN-001")
        fa2 = make_firearm(db, serial_number="GUN-002")
        make_permission(db, guard1.id, fa1.id)
        make_permission(db, guard2.id, fa2.id)
        e1 = _issue(db, guard1, fa1, user)
        e2 = _issue(db, guard2, fa2, user)
        assert e1.firearm_id == fa1.id
        assert e2.firearm_id == fa2.id


class TestReturnFlow:
    def test_return_removes_from_register(self, db):
        user = make_user(db)
        guard = make_guard(db)
        firearm = make_firearm(db)
        make_permission(db, guard.id, firearm.id)
        _issue(db, guard, firearm, user)

        svc.return_firearm(db, firearm.id, user.id)

        from app.models.register import Register
        remaining = db.query(Register).all()
        assert len(remaining) == 0

    def test_return_creates_history_entry(self, db):
        user = make_user(db)
        guard = make_guard(db)
        firearm = make_firearm(db)
        make_permission(db, guard.id, firearm.id)
        _issue(db, guard, firearm, user)
        svc.return_firearm(db, firearm.id, user.id)

        from app.models.register_history import RegisterHistory
        history = db.query(RegisterHistory).order_by(RegisterHistory.actioned_at).all()
        assert len(history) == 2
        assert history[0].action.lower() == "issued"
        assert history[1].action.lower() == "returned"

    def test_reissue_after_return_succeeds(self, db):
        """Firearm returned → can be issued again to same or different guard."""
        user = make_user(db)
        guard = make_guard(db)
        firearm = make_firearm(db)
        make_permission(db, guard.id, firearm.id)

        _issue(db, guard, firearm, user)
        svc.return_firearm(db, firearm.id, user.id)
        entry = _issue(db, guard, firearm, user)  # should not raise
        assert entry.guard_id == guard.id

    def test_return_nonexistent_firearm_raises_404(self, db):
        user = make_user(db)
        with pytest.raises(HTTPException) as exc:
            svc.return_firearm(db, "nonexistent-id", user.id)
        assert exc.value.status_code == 404
