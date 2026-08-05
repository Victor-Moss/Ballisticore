"""
Integration tests — Guards API (/api/guards)
"""
import pytest
from tests.conftest import make_user, make_guard, make_firearm, make_permission, auth_headers


@pytest.fixture
def headers(db):
    user = make_user(db)
    return auth_headers(user.id)


class TestListGuards:
    def test_returns_empty_list(self, client, db, headers):
        res = client.get("/api/guards/", headers=headers)
        assert res.status_code == 200
        assert res.json() == []

    def test_returns_active_guards(self, client, db, headers):
        make_guard(db)
        res = client.get("/api/guards/", headers=headers)
        assert res.status_code == 200
        assert len(res.json()) == 1

    def test_excludes_inactive_by_default(self, client, db, headers):
        make_guard(db, is_active=True, id_number="1111111111111")
        make_guard(db, is_active=False, id_number="2222222222222")
        res = client.get("/api/guards/", headers=headers)
        assert len(res.json()) == 1

    def test_include_inactive_flag(self, client, db, headers):
        make_guard(db, is_active=True, id_number="1111111111111")
        make_guard(db, is_active=False, id_number="2222222222222")
        res = client.get("/api/guards/?include_inactive=true", headers=headers)
        assert len(res.json()) == 2


class TestCreateGuard:
    def test_create_guard_success(self, client, db, headers):
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "id_number": "9001015009087",
            "psira_number": "PS9999999",
        }
        res = client.post("/api/guards/", json=payload, headers=headers)
        assert res.status_code in (200, 201)
        body = res.json()
        assert body["first_name"] == "Alice"
        assert body["is_active"] is True

    def test_create_guard_missing_required_field(self, client, db, headers):
        res = client.post("/api/guards/", json={"last_name": "Smith"}, headers=headers)
        assert res.status_code == 422

    def test_duplicate_id_number_blocked(self, client, db, headers):
        make_guard(db, id_number="9001015009087")
        payload = {"first_name": "Bob", "last_name": "Jones", "id_number": "9001015009087"}
        res = client.post("/api/guards/", json=payload, headers=headers)
        assert res.status_code == 409


class TestCreateGuardWithFirearms:
    """Firearms can be assigned inline while creating the guard, in the same
    transaction. Assigning later from the edit screen still works unchanged."""

    def _payload(self, **overrides):
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "id_number": "9001015009087",
            "psira_number": "PS9999999",
        }
        payload.update(overrides)
        return payload

    def test_assigns_firearm_inline(self, client, db, headers):
        fa = make_firearm(db, serial_number="HG-1", firearm_type="handgun")
        res = client.post("/api/guards/", headers=headers, json=self._payload(
            permitted_handgun=True, firearm_ids=[fa.id]))
        assert res.status_code in (200, 201)
        guard_id = res.json()["id"]

        perms = client.get(f"/api/permissions/guard/{guard_id}", headers=headers).json()
        assert [p["firearm_id"] for p in perms] == [fa.id]
        assert perms[0]["is_permitted"] is True

    def test_multiple_weapon_types_each_get_a_firearm(self, client, db, headers):
        handgun = make_firearm(db, serial_number="HG-2", firearm_type="handgun")
        shotgun = make_firearm(db, serial_number="SG-1", firearm_type="shotgun")
        res = client.post("/api/guards/", headers=headers, json=self._payload(
            permitted_handgun=True, permitted_shotgun=True,
            firearm_ids=[handgun.id, shotgun.id]))
        assert res.status_code in (200, 201)

        perms = client.get(f"/api/permissions/guard/{res.json()['id']}", headers=headers).json()
        assert {p["firearm_id"] for p in perms} == {handgun.id, shotgun.id}

    def test_weapon_type_selected_but_no_firearm_available(self, client, db, headers):
        """Empty inventory must not block guard creation — the guard is created
        with the clearance and no assignment."""
        res = client.post("/api/guards/", headers=headers, json=self._payload(
            permitted_handgun=True, firearm_ids=[]))
        assert res.status_code in (200, 201)
        body = res.json()
        assert body["permitted_handgun"] is True

        perms = client.get(f"/api/permissions/guard/{body['id']}", headers=headers).json()
        assert perms == []

    def test_firearm_ids_is_optional(self, client, db, headers):
        """Callers that never send the field keep working."""
        res = client.post("/api/guards/", headers=headers, json=self._payload())
        assert res.status_code in (200, 201)

    def test_duplicate_ids_collapse(self, client, db, headers):
        fa = make_firearm(db, serial_number="HG-3", firearm_type="handgun")
        res = client.post("/api/guards/", headers=headers, json=self._payload(
            permitted_handgun=True, firearm_ids=[fa.id, fa.id]))
        assert res.status_code in (200, 201)

        perms = client.get(f"/api/permissions/guard/{res.json()['id']}", headers=headers).json()
        assert len(perms) == 1

    def test_unknown_firearm_rejected_and_guard_not_created(self, client, db, headers):
        res = client.post("/api/guards/", headers=headers, json=self._payload(
            permitted_handgun=True, firearm_ids=["no-such-firearm"]))
        assert res.status_code == 404
        assert client.get("/api/guards/", headers=headers).json() == []

    def test_firearm_type_without_clearance_rejected(self, client, db, headers):
        """A shotgun assigned to a guard with no shotgun clearance could never be
        issued — reject it at creation rather than storing a dead assignment."""
        fa = make_firearm(db, serial_number="SG-2", firearm_type="shotgun")
        res = client.post("/api/guards/", headers=headers, json=self._payload(
            permitted_handgun=True, firearm_ids=[fa.id]))
        assert res.status_code == 400
        assert "shotgun" in res.json()["detail"]
        assert client.get("/api/guards/", headers=headers).json() == []

    def test_inactive_firearm_rejected(self, client, db, headers):
        fa = make_firearm(db, serial_number="HG-4", firearm_type="handgun", is_active=False)
        res = client.post("/api/guards/", headers=headers, json=self._payload(
            permitted_handgun=True, firearm_ids=[fa.id]))
        assert res.status_code == 400
        assert client.get("/api/guards/", headers=headers).json() == []

    def test_untyped_firearm_needs_no_clearance(self, client, db, headers):
        """Type is only checked when the firearm has one — same rule as issuance."""
        fa = make_firearm(db, serial_number="UNK-1", firearm_type=None)
        res = client.post("/api/guards/", headers=headers, json=self._payload(
            firearm_ids=[fa.id]))
        assert res.status_code in (200, 201)

    def test_editing_assignments_after_creation_still_works(self, client, db, headers):
        """The edit flow is unchanged: add and remove via /api/permissions."""
        first = make_firearm(db, serial_number="HG-5", firearm_type="handgun")
        second = make_firearm(db, serial_number="HG-6", firearm_type="handgun")
        guard_id = client.post("/api/guards/", headers=headers, json=self._payload(
            permitted_handgun=True, firearm_ids=[first.id])).json()["id"]

        added = client.post("/api/permissions/", headers=headers, json={
            "guard_id": guard_id, "firearm_id": second.id, "is_permitted": True})
        assert added.status_code == 201

        perms = client.get(f"/api/permissions/guard/{guard_id}", headers=headers).json()
        assert {p["firearm_id"] for p in perms} == {first.id, second.id}

        original = next(p for p in perms if p["firearm_id"] == first.id)
        assert client.delete(f"/api/permissions/{original['id']}", headers=headers).status_code == 204

        remaining = client.get(f"/api/permissions/guard/{guard_id}", headers=headers).json()
        assert [p["firearm_id"] for p in remaining] == [second.id]

    def test_guard_with_assignments_can_be_deleted(self, client, db, headers):
        """Assignments are authorisation links and go with the guard. Without a
        delete cascade this fails with a 500 IntegrityError."""
        fa = make_firearm(db, serial_number="HG-8", firearm_type="handgun")
        guard_id = client.post("/api/guards/", headers=headers, json=self._payload(
            permitted_handgun=True, firearm_ids=[fa.id])).json()["id"]

        assert client.delete(f"/api/guards/{guard_id}", headers=headers).status_code == 204
        # The firearm itself survives — only the link is removed.
        assert client.get(f"/api/firearms/{fa.id}", headers=headers).status_code == 200

    def test_inline_assignment_is_issuable(self, client, db, headers):
        """End-to-end: a firearm assigned at creation satisfies the issuance
        permission check, so the guard can actually be issued it."""
        from app.services import permissions as perm_svc
        fa = make_firearm(db, serial_number="HG-7", firearm_type="handgun")
        guard_id = client.post("/api/guards/", headers=headers, json=self._payload(
            permitted_handgun=True, firearm_ids=[fa.id])).json()["id"]

        assert perm_svc.is_guard_permitted(db, guard_id, fa.id) is True


class TestAssignmentPermissionGate:
    """Assigning a firearm is a staff-management action and requires
    perm_manage_staff wherever it happens — inline at creation and via the edit
    flow alike."""

    @pytest.fixture
    def operator(self, db):
        """A logged-in user with no granular permissions."""
        return make_user(db, username="operator", is_admin=False)

    def test_grant_requires_perm_manage_staff(self, client, db, operator):
        guard = make_guard(db)
        fa = make_firearm(db, serial_number="GATE-1")
        res = client.post("/api/permissions/", headers=auth_headers(operator.id), json={
            "guard_id": guard.id, "firearm_id": fa.id, "is_permitted": True})
        assert res.status_code == 403

    def test_revoke_requires_perm_manage_staff(self, client, db, operator, headers):
        guard = make_guard(db)
        fa = make_firearm(db, serial_number="GATE-2")
        perm = client.post("/api/permissions/", headers=headers, json={
            "guard_id": guard.id, "firearm_id": fa.id, "is_permitted": True}).json()

        res = client.delete(f"/api/permissions/{perm['id']}", headers=auth_headers(operator.id))
        assert res.status_code == 403

    def test_reading_permissions_stays_open(self, client, db, operator):
        """Read endpoints are unchanged — only mutations were gated."""
        guard = make_guard(db)
        res = client.get(f"/api/permissions/guard/{guard.id}", headers=auth_headers(operator.id))
        assert res.status_code == 200

    def test_granted_permission_allows_assignment(self, client, db):
        """A non-admin who holds perm_manage_staff works exactly as before."""
        manager = make_user(db, username="manager", is_admin=False)
        manager.perm_manage_staff = True
        db.commit()
        guard = make_guard(db)
        fa = make_firearm(db, serial_number="GATE-3")

        res = client.post("/api/permissions/", headers=auth_headers(manager.id), json={
            "guard_id": guard.id, "firearm_id": fa.id, "is_permitted": True})
        assert res.status_code == 201


class TestEditFlowClearanceValidation:
    """The edit-flow assignment path enforces the same weapon-type clearance
    rule as the creation path."""

    def test_assigning_without_clearance_is_rejected(self, client, db, headers):
        guard = make_guard(db)  # no permitted_* flags set
        fa = make_firearm(db, serial_number="SG-EDIT", firearm_type="shotgun")

        res = client.post("/api/permissions/", headers=headers, json={
            "guard_id": guard.id, "firearm_id": fa.id, "is_permitted": True})
        assert res.status_code == 400
        assert "shotgun" in res.json()["detail"]

    def test_assigning_with_clearance_succeeds(self, client, db, headers):
        guard = make_guard(db)
        guard.permitted_shotgun = True
        db.commit()
        fa = make_firearm(db, serial_number="SG-EDIT-2", firearm_type="shotgun")

        res = client.post("/api/permissions/", headers=headers, json={
            "guard_id": guard.id, "firearm_id": fa.id, "is_permitted": True})
        assert res.status_code == 201

    def test_untyped_firearm_needs_no_clearance(self, client, db, headers):
        """Matches the creation path's exception for firearms with no type."""
        guard = make_guard(db)
        fa = make_firearm(db, serial_number="UNK-EDIT", firearm_type=None)

        res = client.post("/api/permissions/", headers=headers, json={
            "guard_id": guard.id, "firearm_id": fa.id, "is_permitted": True})
        assert res.status_code == 201

    def test_inactive_firearm_is_rejected(self, client, db, headers):
        guard = make_guard(db)
        fa = make_firearm(db, serial_number="OLD-EDIT", is_active=False)

        res = client.post("/api/permissions/", headers=headers, json={
            "guard_id": guard.id, "firearm_id": fa.id, "is_permitted": True})
        assert res.status_code == 400

    def test_existing_permissions_are_not_invalidated(self, client, db, headers):
        """Validation applies to new attempts only. A permission stored before
        the rule existed stays readable and keeps working at issuance."""
        from app.services import permissions as perm_svc
        guard = make_guard(db)  # no shotgun clearance
        fa = make_firearm(db, serial_number="SG-LEGACY", firearm_type="shotgun")
        make_permission(db, guard.id, fa.id)  # written directly, bypassing the API

        perms = client.get(f"/api/permissions/guard/{guard.id}", headers=headers).json()
        assert [p["firearm_id"] for p in perms] == [fa.id]
        assert perm_svc.is_guard_permitted(db, guard.id, fa.id) is True

    def test_revoking_an_uncleared_assignment_is_allowed(self, client, db, headers):
        """Clearance gates granting, never revoking — otherwise a legacy
        assignment could not be cleaned up."""
        guard = make_guard(db)
        fa = make_firearm(db, serial_number="SG-LEGACY-2", firearm_type="shotgun")
        perm = make_permission(db, guard.id, fa.id)

        assert client.delete(f"/api/permissions/{perm.id}", headers=headers).status_code == 204

        res = client.post("/api/permissions/", headers=headers, json={
            "guard_id": guard.id, "firearm_id": fa.id, "is_permitted": False})
        assert res.status_code == 201


class TestDeleteGuardWithHistory:
    """Issue history and permits are compliance records — a guard carrying any
    of them can only be deactivated, never hard-deleted."""

    def _issue(self, db, guard, firearm):
        """Put the guard's firearm on the register (the 'currently issued' state)."""
        from app.models.register import Register
        entry = Register(guard_id=guard.id, firearm_id=firearm.id,
                         issued_by=make_user(db, username=f"iss-{firearm.serial_number}").id)
        db.add(entry)
        db.commit()
        return entry

    def test_guard_without_history_is_still_deletable(self, client, db, headers):
        guard = make_guard(db)
        assert client.delete(f"/api/guards/{guard.id}", headers=headers).status_code == 204

    def test_guard_with_register_entry_cannot_be_deleted(self, client, db, headers):
        guard = make_guard(db)
        fa = make_firearm(db, serial_number="DEL-1")
        self._issue(db, guard, fa)

        res = client.delete(f"/api/guards/{guard.id}", headers=headers)
        assert res.status_code == 409  # currently issued — return it first
        assert "issued" in res.json()["detail"]
        assert client.get(f"/api/guards/{guard.id}", headers=headers).status_code == 200

    def test_guard_with_history_entry_cannot_be_deleted(self, client, db, headers):
        from app.models.register_history import RegisterHistory
        guard = make_guard(db)
        fa = make_firearm(db, serial_number="DEL-2")
        db.add(RegisterHistory(guard_id=guard.id, firearm_id=fa.id, action="RETURNED",
                               actioned_by=make_user(db, username="act").id))
        db.commit()

        res = client.delete(f"/api/guards/{guard.id}", headers=headers)
        assert res.status_code == 400
        assert "Deactivate" in res.json()["detail"]
        assert client.get(f"/api/guards/{guard.id}", headers=headers).status_code == 200

    def test_guard_with_permit_cannot_be_deleted(self, client, db, headers):
        from app.models.permit import Permit
        guard = make_guard(db)
        fa = make_firearm(db, serial_number="DEL-3")
        db.add(Permit(permit_number="BC-DEL-3", guard_id=guard.id, firearm_id=fa.id,
                      issued_by=make_user(db, username="iss3").id))
        db.commit()

        res = client.delete(f"/api/guards/{guard.id}", headers=headers)
        assert res.status_code == 400
        assert "Deactivate" in res.json()["detail"]

    def test_permissions_alone_do_not_block_deletion(self, client, db, headers):
        """Authorisation links are not audit history — they still cascade."""
        guard = make_guard(db)
        fa = make_firearm(db, serial_number="DEL-4")
        make_permission(db, guard.id, fa.id)

        assert client.delete(f"/api/guards/{guard.id}", headers=headers).status_code == 204

    def test_deactivating_a_guard_with_history_preserves_records(self, client, db, headers):
        from app.models.register_history import RegisterHistory
        guard = make_guard(db)
        fa = make_firearm(db, serial_number="DEL-5")
        make_permission(db, guard.id, fa.id)
        db.add(RegisterHistory(guard_id=guard.id, firearm_id=fa.id, action="RETURNED",
                               actioned_by=make_user(db, username="act5").id))
        db.commit()

        res = client.put(f"/api/guards/{guard.id}/deactivate", headers=headers)
        assert res.status_code == 200
        assert res.json()["is_active"] is False

        # History intact and still queryable.
        assert db.query(RegisterHistory).filter(RegisterHistory.guard_id == guard.id).count() == 1
        # Out of the default guard list, so unavailable for new issuance...
        assert guard.id not in [g["id"] for g in client.get("/api/guards/", headers=headers).json()]
        # ...but still retrievable for its history.
        assert client.get(f"/api/guards/{guard.id}", headers=headers).status_code == 200

    def test_deactivated_guard_cannot_be_issued_a_firearm(self, client, db, headers):
        """Deactivation is a real substitute for deletion: issuance refuses."""
        from fastapi import HTTPException
        from app.services import issuance
        guard = make_guard(db, is_active=False)
        fa = make_firearm(db, serial_number="DEL-6")
        make_permission(db, guard.id, fa.id)

        with pytest.raises(HTTPException) as exc:
            issuance.issue_firearm(db, guard.id, fa.id, issued_by=make_user(db, username="iss6").id)
        assert exc.value.status_code == 400
        assert "not active" in exc.value.detail


class TestDeactivateReactivate:
    def test_deactivate_guard(self, client, db, headers):
        guard = make_guard(db)
        res = client.put(f"/api/guards/{guard.id}/deactivate", headers=headers)
        assert res.status_code == 200
        assert res.json()["is_active"] is False

    def test_reactivate_guard(self, client, db, headers):
        guard = make_guard(db, is_active=False)
        res = client.put(f"/api/guards/{guard.id}/reactivate", headers=headers)
        assert res.status_code == 200
        assert res.json()["is_active"] is True

    def test_deactivate_nonexistent_returns_404(self, client, db, headers):
        res = client.put("/api/guards/bad-id/deactivate", headers=headers)
        assert res.status_code == 404
