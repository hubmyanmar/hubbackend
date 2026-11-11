from typing import Optional

from pydantic import BaseModel


class BookingRulesOut(BaseModel):
    approval_required: bool
    work_start: str
    work_end: str
    notify_email: bool
    notify_in_app: bool
    notify_zoho_cliq: bool
    approver_admin: bool
    approver_approver: bool


class BookingRulesUpdate(BaseModel):
    approval_required: bool
    work_start: str
    work_end: str
    notify_email: bool
    notify_in_app: bool
    notify_zoho_cliq: bool
    approver_admin: bool
    approver_approver: bool


class CalendarIntegrationsUpdate(BaseModel):
    zoho_enabled: bool


class MeetingRecordsRetention(BaseModel):
    retention_days: Optional[int]


class MeetingRecordsRetentionUpdate(BaseModel):
    retention_days: Optional[int]


class NotificationPreferencesUpdate(BaseModel):
    email_enabled: bool
    inapp_enabled: bool
    cliq_enabled: bool


class NotificationPreferencesOut(BaseModel):
    email_enabled: bool
    inapp_enabled: bool
    cliq_enabled: bool
