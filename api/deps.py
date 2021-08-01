from crud.crud_user import CRUDUser
from schemas.token import TokenPayload
from models.user import User
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

import models
from core import security
from core.config import settings
from db.session import SessionLocal

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API}/login/access-token")


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


user1 = CRUDUser(User)


def get_current_user(db: Session = Depends(get_db),
                     token: str = Depends(reusable_oauth2)) -> User:
    try:
        payload = jwt.decode(token,
                             settings.SECRET_KEY,
                             algorithms=[security.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = user1.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_current_active_user(
        current_user: models.user.User = Depends(get_current_user), ) -> User:
    if not user1.is_active(current_user):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_active_superuser(
        current_user: models.user.User = Depends(get_current_user), ) -> User:
    if not user1.is_superuser(current_user):
        raise HTTPException(status_code=400,
                            detail="The user doesn't have enough privileges")
    return current_user