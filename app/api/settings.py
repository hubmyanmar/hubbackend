import re
from datetime import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.booking_rule import BookingRule
from app.models.notification_preference import NotificationPreference
from app.schemas.booking_rule import (
    CalendarIntegrationsUpdate,
    BookingRulesOut,
    BookingRulesUpdate,
    NotificationPreferencesOut,
    NotificationPreferencesUpdate,
)

router = APIRouter(prefix="/settings", tags=["Settings"])

DEFAULTS = {
    "approval_required": True,
    "work_start": "09:00",
    "work_end": "18:00",
    "notify_email": True,
    "notify_in_app": True,
    "notify_zoho_cliq": True,
    "zoho_enabled": True,
    "approver_admin": True,
    "approver_approver": True,
}


def _format_time(value: time) -> str:
    return value.strftime("%H:%M")


def _to_response(rule: BookingRule) -> BookingRulesOut:
    return BookingRulesOut(
        approval_required=rule.approval_required,
        work_start=_format_time(rule.work_start),
        work_end=_format_time(rule.work_end),
        notify_email=rule.notify_email,
        notify_in_app=rule.notify_in_app,
        notify_zoho_cliq=rule.notify_zoho_cliq,
        approver_admin=rule.approver_admin,
        approver_approver=rule.approver_approver,
    )


def _parse_time(value: str, field_name: str) -> time:
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be a valid 24-hour time in HH:MM format",
        )
    hour, minute = map(int, value.split(":"))
    return time(hour=hour, minute=minute)


@router.get("/booking-rules", response_model=BookingRulesOut)
def read_booking_rules(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rule = db.query(BookingRule).filter(BookingRule.id == 1).first()
    if rule is None:
        return BookingRulesOut(**DEFAULTS)
    return _to_response(rule)


@router.put("/booking-rules", response_model=BookingRulesOut)
def update_booking_rules(
    rules_in: BookingRulesUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    work_start = _parse_time(rules_in.work_start, "work_start")
    work_end = _parse_time(rules_in.work_end, "work_end")
    if not rules_in.approver_admin and not rules_in.approver_approver:
        raise HTTPException(
            status_code=400,
            detail="At least one approver role must be selected",
        )
    if work_end <= work_start:
        raise HTTPException(status_code=400, detail="work_end must be after work_start")

    rule = db.query(BookingRule).filter(BookingRule.id == 1).first()
    if rule is None:
        rule = BookingRule(id=1)
        db.add(rule)

    rule.approval_required = rules_in.approval_required
    rule.work_start = work_start
    rule.work_end = work_end
    rule.notify_email = rules_in.notify_email
    rule.notify_in_app = rules_in.notify_in_app
    rule.notify_zoho_cliq = rules_in.notify_zoho_cliq
    rule.approver_admin = rules_in.approver_admin
    rule.approver_approver = rules_in.approver_approver

    db.commit()
    db.refresh(rule)
    return _to_response(rule)


@router.get("/calendar-integrations")
def read_calendar_integrations(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rule = db.query(BookingRule).filter(BookingRule.id == 1).first()
    zoho_enabled = rule.zoho_enabled if rule is not None else DEFAULTS["zoho_enabled"]
    try:
        from app.utils.zoho_sync import get_access_token

        zoho_connected = bool(get_access_token())
    except Exception:
        zoho_connected = False
    return {"zoho_enabled": zoho_enabled, "zoho_connected": zoho_connected}


@router.put("/calendar-integrations")
def update_calendar_integrations(
    integrations_in: CalendarIntegrationsUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    rule = db.query(BookingRule).filter(BookingRule.id == 1).first()
    if rule is None:
        rule = BookingRule(id=1)
        db.add(rule)

    rule.zoho_enabled = integrations_in.zoho_enabled

    db.commit()
    db.refresh(rule)
    return {"zoho_enabled": rule.zoho_enabled}


@router.get("/notification-preferences", response_model=NotificationPreferencesOut)
def read_notification_preferences(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    preference = (
        db.query(NotificationPreference)
        .filter(NotificationPreference.user_id == current_user.id)
        .first()
    )
    if preference is None:
        return NotificationPreferencesOut(
            email_enabled=True,
            inapp_enabled=True,
            cliq_enabled=False,
        )
    return NotificationPreferencesOut(
        email_enabled=preference.email_enabled,
        inapp_enabled=preference.inapp_enabled,
        cliq_enabled=preference.cliq_enabled,
    )


@router.put("/notification-preferences", response_model=NotificationPreferencesOut)
def update_notification_preferences(
    preferences_in: NotificationPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    preference = (
        db.query(NotificationPreference)
        .filter(NotificationPreference.user_id == current_user.id)
        .first()
    )
    if preference is None:
        preference = NotificationPreference(user_id=current_user.id)
        db.add(preference)

    preference.email_enabled = preferences_in.email_enabled
    preference.inapp_enabled = preferences_in.inapp_enabled
    preference.cliq_enabled = preferences_in.cliq_enabled

    db.commit()
    db.refresh(preference)
    return NotificationPreferencesOut(
        email_enabled=preference.email_enabled,
        inapp_enabled=preference.inapp_enabled,
        cliq_enabled=preference.cliq_enabled,
    )
