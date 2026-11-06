from sqlalchemy import Boolean, Column, DateTime, Integer, Time, func

from app.core.database import Base


class BookingRule(Base):
    __tablename__ = "booking_rules"

    id = Column(Integer, primary_key=True)
    approval_required = Column(Boolean, nullable=False, server_default="true")
    work_start = Column(Time, nullable=False, server_default="09:00")
    work_end = Column(Time, nullable=False, server_default="18:00")
    notify_email = Column(Boolean, nullable=False, server_default="true")
    notify_in_app = Column(Boolean, nullable=False, server_default="true")
    notify_zoho_cliq = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
