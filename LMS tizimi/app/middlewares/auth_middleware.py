from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from ..core.security import SECRET_KEY, ALGORITHM # security.py faylidan import
from ..core.database import get_db
from .. import services, schemas, models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credentiallarni tasdiqlashda xatolik",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = schemas.TokenPayload(**payload)
    except ValidationError:
        raise credentials_exception
    except jwt.JWTError: # JWT Decode xatosi uchun
        raise credentials_exception
    user = services.get_user(db, user_id=int(user_id))
    if user is None:
        raise credentials_exception
    return user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: models.User = Depends(get_current_user)):
        if current_user.role.name not in self.allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sizda ruxsat yetarli emas")