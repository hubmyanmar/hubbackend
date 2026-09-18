from sqlalchemy import Column, BigInteger, String, ForeignKeyConstraint, TIMESTAMP, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"
    __table_args__ = (
        ForeignKeyConstraint(
            ['meeting_id'], 
            ['meetings.id'], 
            ondelete='CASCADE',
            name='fk_meeting_participants_meeting_id'
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    meeting_id = Column(BigInteger, nullable=False)  # inline ForeignKey ကို ဖြုတ်လိုက်ပါပြီ
    zoho_user_id = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=False)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to Meeting
    meeting = relationship("Meeting", backref="participants_list", foreign_keys=[meeting_id])