import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
# engine နှင့် Base ကိုပါ import လုပ်ပေးပါ
from app.core.database import SessionLocal, engine, Base 
from app.models.meeting_room import MeetingRoom

INITIAL_ROOMS = [
    {
        "name": "MD Room",
        "capacity": 8,
        "status": "active",
        "devices": ["Projector 4K", "Smart TV", "Whiteboard"]
    },
    {
        "name": "Bagan Room",
        "capacity": 12,
        "status": "active",
        "devices": ["Smart TV", "Mic System", "Video Conference"]
    },
    {
        "name": "Konebaung Room",
        "capacity": 6,
        "status": "active",
        "devices": ["TV Screen", "Whiteboard"]
    },
    {
        "name": "BOD Home",
        "capacity": 20,
        "status": "active",
        "devices": ["Projector 4K", "Smart TV", "Premium Mic", "Speakers", "Whiteboard"]
    }
]

def seed_meeting_rooms(db: Session):
    # Table မရှိသေးပါက အလိုအလျောက် ဖန်တီးပေးမည့် መስလိုင်း
    Base.metadata.create_all(bind=engine)

    print("🌱 Seeding meeting rooms into database...")
    
    for room_data in INITIAL_ROOMS:
        existing_room = db.query(MeetingRoom).filter(MeetingRoom.name == room_data["name"]).first()
        
        if not existing_room:
            new_room = MeetingRoom(
                name=room_data["name"],
                capacity=room_data["capacity"],
                status=room_data["status"],
                devices=room_data["devices"]
            )
            db.add(new_room)
            print(f" Added room: {room_data['name']}")
        else:
            print(f" Room already exists: {room_data['name']}")
            
    db.commit()
    print(" Meeting rooms seeding completed successfully!")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_meeting_rooms(db)
    finally:
        db.close()