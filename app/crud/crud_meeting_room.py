# app/crud/crud_meeting_room.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.meeting_room import MeetingRoom
from app.schemas.meeting_room import MeetingRoomCreate, MeetingRoomUpdate


# 1. Meeting Room အားလုံးကို ဆွဲထုတ်ခြင်း (Select All)
def get_meeting_rooms(db: Session, skip: int = 0, limit: int = 100) -> List[MeetingRoom]:
    return db.query(MeetingRoom).offset(skip).limit(limit).all()


# 2. ID ဖြင့် အခန်းတစ်ခုတည်းကို ရှာခြင်း (Select By ID)
def get_meeting_room_by_id(db: Session, room_id: int) -> Optional[MeetingRoom]:
    return db.query(MeetingRoom).filter(MeetingRoom.id == room_id).first()


# 3. အခန်းအသစ် ထည့်သွင်းခြင်း (Insert / Create)
def create_meeting_room(db: Session, room_in: MeetingRoomCreate) -> MeetingRoom:
    db_room = MeetingRoom(
        name=room_in.name,
        capacity=room_in.capacity,
        status=room_in.status,
        devices=room_in.devices
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room


# 4. အခန်းအချက်အလက် ပြင်ဆင်ခြင်း (Update)
def update_meeting_room(db: Session, db_room: MeetingRoom, room_in: MeetingRoomUpdate) -> MeetingRoom:
    # Pydantic v2 သုံးထားပါက model_dump၊ v1 ဆိုပါက dict() သုံးပါ
    update_data = room_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_room, field, value)
    
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room


# 5. အခန်း ဖျက်ခြင်း (Delete)
def delete_meeting_room(db: Session, room_id: int) -> Optional[MeetingRoom]:
    db_room = db.query(MeetingRoom).filter(MeetingRoom.id == room_id).first()
    if db_room:
        db.delete(db_room)
        db.commit()
    return db_room