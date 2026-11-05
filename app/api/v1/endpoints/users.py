import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.crud import crud_user
from app.models.user import User
from app.schemas.user import ActiveUpdate, RoleUpdate, UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserOut])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return crud_user.get_users(db, skip=skip, limit=limit)


@router.put("/profile/image", response_model=UserOut)
def update_profile_image(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    လက်ရှိ Login ဝင်ထားသော User ၏ Profile ပုံ သို့မဟုတ် အချက်အလက်များကို Update လုပ်ရန်
    """
    return crud_user.update_user(db, db_user=current_user, user=user_update)


@router.get("/{user_id}", response_model=UserOut)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    db_user = crud_user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    db_user = crud_user.get_user_by_email(db, email=str(user.email))
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    return crud_user.create_user(db, user)


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own profile")

    db_user = crud_user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.email is not None:
        existing_user = crud_user.get_user_by_email(db, email=str(user.email))
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    return crud_user.update_user(db, db_user, user)


@router.patch("/{user_id}/role", response_model=UserOut)
def update_user_role(
    user_id: int,
    role_update: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    db_user = crud_user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if db_user.role == "admin" and role_update.role != "admin":
        admin_count = db.query(User).filter(User.role == "admin").count()
        if admin_count == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The last admin cannot be demoted",
            )

    db_user.role = role_update.role
    db.commit()
    db.refresh(db_user)
    return db_user


@router.patch("/{user_id}/active", response_model=UserOut)
def update_user_active(
    user_id: int,
    active_update: ActiveUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    db_user = crud_user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not active_update.is_active and db_user.role == "admin":
        admin_count = db.query(User).filter(User.role == "admin").count()
        if admin_count == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The last admin cannot be deactivated",
            )

    db_user.is_active = active_update.is_active
    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    db_user = crud_user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    crud_user.delete_user(db, db_user)
    return None