from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import action_item as action_crud
from app.db.session import get_db
from app.schemas import action_item as action_schemas

router = APIRouter(prefix="/action-items", tags=["action_items"])


@router.post("/", response_model=action_schemas.ActionItemOut, status_code=status.HTTP_201_CREATED)
def create_action_item(payload: action_schemas.ActionItemCreate, db: Session = Depends(get_db)):
    meeting = db.execute("SELECT 1 FROM meetings WHERE id = :id", {"id": payload.meeting_id}).first()
    if meeting is None:
        raise HTTPException(status_code=400, detail="meeting_id not found")
    return action_crud.create_action_item(db=db, payload=payload)


@router.get("/", response_model=List[action_schemas.ActionItemOut])
def read_action_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return action_crud.list_action_items(db=db, skip=skip, limit=limit)


@router.get("/meetings/{meeting_id}", response_model=List[action_schemas.ActionItemOut])
def read_action_items_by_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.execute("SELECT 1 FROM meetings WHERE id = :id", {"id": meeting_id}).first()
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return action_crud.list_action_items_by_meeting(db=db, meeting_id=meeting_id)


@router.get("/{action_item_id}", response_model=action_schemas.ActionItemOut)
def read_action_item(action_item_id: int, db: Session = Depends(get_db)):
    obj = action_crud.get_action_item(db=db, action_item_id=action_item_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Action item not found")
    return obj


@router.put("/{action_item_id}", response_model=action_schemas.ActionItemOut)
def update_action_item(
    action_item_id: int,
    updates: action_schemas.ActionItemUpdate,
    db: Session = Depends(get_db),
):
    obj = action_crud.get_action_item(db=db, action_item_id=action_item_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Action item not found")
    return action_crud.update_action_item(db=db, db_obj=obj, updates=updates)


@router.delete("/{action_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_action_item(action_item_id: int, db: Session = Depends(get_db)):
    obj = action_crud.get_action_item(db=db, action_item_id=action_item_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Action item not found")
    action_crud.delete_action_item(db=db, db_obj=obj)
    return None
