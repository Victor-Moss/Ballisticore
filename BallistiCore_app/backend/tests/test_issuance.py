"""
Unit tests — Issuance engine (services/issuance.py)
All tests run against in-memory SQLite — no real DB touched.
"""
import pytest
from fastapi import HTTPException
from tests.conftest import make_user, make_guard, make_firearm, make_permission
from app.services import issuance as svc


# make_user()'s default password — used to satisfy the issuer/staff e-signature.
PASSWORD = "testpass"


def _issue(db, guard, firearm, user, guard_password=None):
    """Helper: issue a firearm and return the register entry.

    The issuing staff member's e-signature (current_user + their password) is
    mandatory on every issue, so it's supplied here. Guards created via
    make_guard have no sign-in account, so no guard signature is required;
    pass guard_password when the guard has an account and must sign."""
    return svc.issue_firearm(db, guard.id, firearm.id, user.id,
                             current_user=user, issuer_password=PASSWORD,
                             guard_password=guard_password)


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

        svc.return_firearm(db, firearm.id, user.id, current_user=user, staff_password=PASSWORD)

        from app.models.register import Register
        remaining = db.query(Register).all()
        assert len(remaining) == 0

    def test_return_creates_history_entry(self, db):
        user = make_user(db)
        guard = make_guard(db)
        firearm = make_firearm(db)
        make_permission(db, guard.id, firearm.id)
        _issue(db, guard, firearm, user)
        svc.return_firearm(db, firearm.id, user.id, current_user=user, staff_password=PASSWORD)

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
        svc.return_firearm(db, firearm.id, user.id, current_user=user, staff_password=PASSWORD)
        entry = _issue(db, guard, firearm, user)  # should not raise
        assert entry.guard_id == guard.id

    def test_return_nonexistent_firearm_raises_404(self, db):
        user = make_user(db)
        with pytest.raises(HTTPException) as exc:
            svc.return_firearm(db, "nonexistent-id", user.id)
        assert exc.value.status_code == 404


class TestReturnSignatureEnforcement:
    """Dual e-signature is mandatory on return (FCA / PSIRA). The return must be
    blocked and nothing mutated if either required signature is missing/wrong."""

    def _issue_and_register_intact(self, db):
        user = make_user(db)
        guard = make_guard(db)
        firearm = make_firearm(db)
        make_permission(db, guard.id, firearm.id)
        _issue(db, guard, firearm, user)
        return user, guard, firearm

    def _register_count(self, db):
        from app.models.register import Register
        return db.query(Register).count()

    def test_return_blocked_without_staff_signature(self, db):
        """No staff password → 400 and the firearm stays issued."""
        user, _guard, firearm = self._issue_and_register_intact(db)
        with pytest.raises(HTTPException) as exc:
            svc.return_firearm(db, firearm.id, user.id, current_user=user)
        assert exc.value.status_code == 400
        assert self._register_count(db) == 1  # nothing removed

    def test_return_blocked_with_wrong_staff_password(self, db):
        """Wrong staff password → 403 and the firearm stays issued."""
        user, _guard, firearm = self._issue_and_register_intact(db)
        with pytest.raises(HTTPException) as exc:
            svc.return_firearm(db, firearm.id, user.id, current_user=user,
                               staff_password="not-the-password")
        assert exc.value.status_code == 403
        assert self._register_count(db) == 1

    def test_return_blocked_when_signed_in_guard_signature_missing(self, db):
        """A guard with a sign-in account must also sign — missing guard
        password → 400 and the firearm stays issued, even though the staff
        member signed correctly."""
        from app.services import guard_auth
        user = make_user(db)
        guard = make_guard(db)
        guard_auth.set_account(db, guard, username="jsmith", password="guardpass")
        firearm = make_firearm(db)
        make_permission(db, guard.id, firearm.id)
        _issue(db, guard, firearm, user, guard_password="guardpass")

        with pytest.raises(HTTPException) as exc:
            svc.return_firearm(db, firearm.id, user.id, current_user=user,
                               staff_password=PASSWORD)  # guard_password omitted
        assert exc.value.status_code == 400
        assert self._register_count(db) == 1

    def test_return_stores_both_signatures_on_permit_and_history(self, db):
        """Happy path with a signed-in guard: both return signatures are
        persisted on the permit and the RETURNED history record."""
        from app.services import guard_auth
        from app.models.permit import Permit
        from app.models.register_history import RegisterHistory
        user = make_user(db)
        guard = make_guard(db)
        guard_auth.set_account(db, guard, username="jsmith2", password="guardpass")
        firearm = make_firearm(db)
        make_permission(db, guard.id, firearm.id)
        _issue(db, guard, firearm, user, guard_password="guardpass")

        svc.return_firearm(db, firearm.id, user.id, current_user=user,
                           staff_password=PASSWORD, guard_password="guardpass")

        permit = db.query(Permit).first()
        assert permit.return_guard_signed and permit.return_guard_signed_at is not None
        assert permit.return_received_signed and permit.return_received_signed_at is not None
        assert permit.return_received_by == user.id

        returned = db.query(RegisterHistory).filter(RegisterHistory.action == "RETURNED").one()
        assert returned.guard_signed and returned.guard_signed_at is not None    # returning guard
        assert returned.issuer_signed and returned.issuer_signed_at is not None  # receiving staff
