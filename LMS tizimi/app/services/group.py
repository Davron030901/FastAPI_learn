from sqlalchemy.orm import Session
from .. import models, schemas  # Import models va schemas parent papkadan

def get_group(db: Session, group_id: int):
    return db.query(models.Group).filter(models.Group.id == group_id).first()

def get_group_by_name(db: Session, name: str):
    return db.query(models.Group).filter(models.Group.name == name).first()

def get_groups(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Group).offset(skip).limit(limit).all()

def create_group(db: Session, group: schemas.GroupCreate):
    db_group = models.Group(**group.dict()) # Pydantic schemani modelga o'tkazamiz
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

def update_group(db: Session, group_id: int, group_update: schemas.GroupUpdate):
    db_group = get_group(db, group_id)
    if not db_group:
        return None
    for key, value in group_update.dict(exclude_unset=True).items():
        setattr(db_group, key, value)
    db.commit()
    db.refresh(db_group)
    return db_group

def delete_group(db: Session, group_id: int):
    db_group = get_group(db, group_id)
    if not db_group:
        return None
    db.delete(db_group)
    db.commit()
    return db_group