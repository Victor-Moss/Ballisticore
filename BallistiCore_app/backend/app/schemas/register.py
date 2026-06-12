from typing import Optional
from datetime import datetime, time
from pydantic import BaseModel
from app.schemas.guard import GuardSummary
from app.schemas.firearm import FirearmSummary


class IssueRequest(BaseModel):
    guard_id: str
    firearm_id: str
    issued_by: str
    notes: Optional[str] = None
    # Permit fields
    rounds_issued: Optional[int] = None
    period_from_time: Optional[time] = None
    valid_until_time: Optional[time] = None
    cit_cell_route: Optional[str] = None
    witness: Optional[str] = None
    saps_competency_number: Optional[str] = None
    # Register fields
    ammunition_issued: Optional[int] = None
    firearm_inspected_correct: Optional[bool] = None
    cit_id: Optional[str] = None
    responsible_person_name: Optional[str] = None
    # Electronic signatures. Both parties sign by entering their own password:
    #   guard_password  — the receiving guard ("Received by"). Required when the
    #                     guard has a sign-in account; ignored otherwise.
    #   issuer_password — the issuing staff member ("Issued by"). Always required;
    #                     verified against the authenticated operator.
    guard_password: Optional[str] = None
    issuer_password: Optional[str] = None


class ReturnRequest(BaseModel):
    firearm_id: str
    actioned_by: str
    notes: Optional[str] = None
    # Permit return fields
    rounds_returned: Optional[int] = None
    firearm_returned_correct: Optional[bool] = None
    in_order: Optional[bool] = None
    remarks: Optional[str] = None
    # History fields
    ammunition_returned: Optional[int] = None
    permit_returned: Optional[bool] = None
    # Electronic signatures on return:
    #   guard_password — the returning guard ("Returned by"). Required when the
    #                    guard has a sign-in account; ignored otherwise.
    #   staff_password — the staff member receiving the return ("Received by").
    #                    Always required; verified against the authenticated operator.
    guard_password: Optional[str] = None
    staff_password: Optional[str] = None


class RegisterEntryOut(BaseModel):
    id: str
    guard_id: str
    firearm_id: str
    issued_by: str
    issued_at: datetime
    permit_id: Optional[str] = None
    ammunition_issued: Optional[int] = None
    ammunition_type: Optional[str] = None
    firearm_inspected_correct: Optional[bool] = None
    cit_id: Optional[str] = None
    responsible_person_name: Optional[str] = None
    guard_signed: bool = False
    guard_signed_at: Optional[datetime] = None
    issuer_signed: bool = False
    issuer_signed_at: Optional[datetime] = None
    guard: Optional[GuardSummary] = None
    firearm: Optional[FirearmSummary] = None

    model_config = {"from_attributes": True}


class HistoryEntryOut(BaseModel):
    id: str
    guard_id: str
    firearm_id: str
    action: str
    actioned_by: str
    actioned_at: datetime
    notes: Optional[str] = None
    ammunition_issued: Optional[int] = None
    ammunition_returned: Optional[int] = None
    ammunition_type: Optional[str] = None
    firearm_inspected_correct: Optional[bool] = None
    firearm_returned_correct: Optional[bool] = None
    permit_returned: Optional[bool] = None
    cit_id: Optional[str] = None
    responsible_person_name: Optional[str] = None
    guard_signed: bool = False
    guard_signed_at: Optional[datetime] = None
    issuer_signed: bool = False
    issuer_signed_at: Optional[datetime] = None
    guard: Optional[GuardSummary] = None
    firearm: Optional[FirearmSummary] = None

    model_config = {"from_attributes": True}
