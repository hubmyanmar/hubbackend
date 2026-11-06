from pydantic import BaseModel


class BookingRulesOut(BaseModel):
    approval_required: bool
    work_start: str
    work_end: str
    notify_email: bool
    notify_in_app: bool
    notify_zoho_cliq: bool


class BookingRulesUpdate(BaseModel):
    approval_required: bool
    work_start: str
    work_end: str
    notify_email: bool
    notify_in_app: bool
    notify_zoho_cliq: bool
