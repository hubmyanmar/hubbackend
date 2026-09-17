# app/api/v1/endpoints/meeting_rooms.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.meeting_room import MeetingRoomCreate, MeetingRoomUpdate, MeetingRoomResponse
from app import crud

router = APIRouter()

@router.get("/", response_model=List[MeetingRoomResponse])
def read_meeting_rooms(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    rooms = crud.crud_meeting_room.get_meeting_rooms(db, skip=skip, limit=limit)
    return rooms

@router.get("/{room_id}", response_model=MeetingRoomResponse)
def read_meeting_room(room_id: int, db: Session = Depends(get_db)):
    db_room = crud.crud_meeting_room.get_meeting_room_by_id(db, room_id=room_id)
    if not db_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting room not found"
        )
    return db_room


@router.post("/", response_model=MeetingRoomResponse, status_code=status.HTTP_201_CREATED)
def create_meeting_room(room_in: MeetingRoomCreate, db: Session = Depends(get_db)):
    return crud.crud_meeting_room.create_meeting_room(db=db, room_in=room_in)


@router.put("/{room_id}", response_model=MeetingRoomResponse)
def update_meeting_room(room_id: int, room_in: MeetingRoomUpdate, db: Session = Depends(get_db)):
    db_room = crud.crud_meeting_room.get_meeting_room_by_id(db, room_id=room_id)
    if not db_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting room not found"
        )
    return crud.crud_meeting_room.update_meeting_room(db=db, db_room=db_room, room_in=room_in)


@router.delete("/{room_id}", status_code=status.HTTP_200_OK)
def delete_meeting_room(room_id: int, db: Session = Depends(get_db)):
    db_room = crud.crud_meeting_room.get_meeting_room_by_id(db, room_id=room_id)
    if not db_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting room not found"
        )
    crud.crud_meeting_room.delete_meeting_room(db=db, room_id=room_id)
    return {"message": "Meeting room deleted successfully"}