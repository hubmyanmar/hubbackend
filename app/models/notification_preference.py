from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, func

from app.core.database import Base


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    email_enabled = Column(Boolean, nullable=False, server_default="true")
    inapp_enabled = Column(Boolean, nullable=False, server_default="true")
    cliq_enabled = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
