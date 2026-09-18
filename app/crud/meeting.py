from sqlalchemy.orm import Session
from datetime import date, time
from app.models.meeting import Meeting
from app.models.meeting_participant import MeetingParticipant
from app.schemas.meeting import MeetingCreate

def check_room_conflict(db: Session, room_id: int, meeting_date: date, start_time: time, end_time: time) -> bool:
    """အခန်းတစ်ခုတည်းတွင် အချိန်ထပ်နေသော Meeting ရှိ/မရှိ စစ်ဆေးခြင်း"""
    existing_meeting = db.query(Meeting).filter(
        Meeting.room_id == room_id,
        Meeting.meeting_date == meeting_date,
        Meeting.start_time < end_time,
        Meeting.end_time > start_time
    ).first()
    return existing_meeting is not None

def create_meeting(db: Session, meeting_in: MeetingCreate) -> Meeting:
    exclude_fields = {"participant_emails"}
    if hasattr(meeting_in, 'participants'):
        exclude_fields.add("participants")
        
    meeting_data = meeting_in.model_dump(exclude=exclude_fields)
    db_meeting = Meeting(**meeting_data)
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)

    if hasattr(meeting_in, 'participant_emails') and meeting_in.participant_emails:
        for email in meeting_in.participant_emails:
            participant = MeetingParticipant(
                meeting_id=db_meeting.id, 
                email=email,
                name="",
                zoho_user_id=""
            )
            db.add(participant)
            
    elif hasattr(meeting_in, 'participants') and meeting_in.participants:
        for p in meeting_in.participants:
            
            p_email = p.get("email") if isinstance(p, dict) else getattr(p, "email", None)
            p_name = p.get("name") if isinstance(p, dict) else getattr(p, "name", "")
            p_zoho_id = p.get("zoho_user_id") if isinstance(p, dict) else getattr(p, "zoho_user_id", "")
            
            if p_email:
                participant = MeetingParticipant(
                    meeting_id=db_meeting.id,
                    zoho_user_id=p_zoho_id,
                    name=p_name,
                    email=p_email
                )
                db.add(participant)
        
    db.commit()
    db.refresh(db_meeting)
    return db_meeting

def list_meetings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Meeting).offset(skip).limit(limit).all()

def get_meeting(db: Session, meeting_id: int):
    return db.query(Meeting).filter(Meeting.id == meeting_id).first()

def delete_meeting(db: Session, db_obj: Meeting):
    db.delete(db_obj)
    db.commit()