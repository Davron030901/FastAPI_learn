from fastapi import APIRouter, Depends, HTTPException
from typing import List

from sqlalchemy.orm import Session

from .. import schemas, services
from ..core.database import get_db

router = APIRouter(prefix="/groups", tags=["Groups"])

@router.post("/", response_model=schemas.GroupSchema, status_code=201)
def create_group(group: schemas.GroupCreate, db: Session = Depends(get_db)):
    db_group = services.get_group_by_name(db, name=group.name)
    if db_group:
        raise HTTPException(status_code=400, detail="Guruh nomi allaqachon mavjud")
    return services.create_group(db=db, group=group)

@router.get("/{group_id}", response_model=schemas.GroupSchema)
def read_group(group_id: int, db: Session = Depends(get_db)):
    db_group = services.get_group(db, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Guruh topilmadi")
    return db_group

@router.get("/", response_model=List[schemas.GroupSchema])
def read_groups(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    groups = services.get_groups(db, skip=skip, limit=limit)
    return groups

@router.put("/{group_id}", response_model=schemas.GroupSchema)
def update_group(group_id: int, group_update: schemas.GroupUpdate, db: Session = Depends(get_db)):
    db_group = services.get_group(db, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Guruh topilmadi")
    return services.update_group(db=db, group_id=group_id, group_update=group_update)

@router.delete("/{group_id}", response_model=dict)
def delete_group(group_id: int, db: Session = Depends(get_db)):
    db_group = services.get_group(db, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Guruh topilmadi")
    return services.delete_group(db=db, group_id=group_id)