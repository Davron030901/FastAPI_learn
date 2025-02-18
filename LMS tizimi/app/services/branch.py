from typing import List

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from .. import models, schemas

def get_branch(db: Session, branch_id: int):
    db_branch = db.query(models.Branch).filter(models.Branch.id == branch_id).first()
    if not db_branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filial topilmadi")
    return db_branch

def get_branch_by_name(db: Session, name: str):
    return db.query(models.Branch).filter(models.Branch.name == name).first()

def get_branches(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Branch).offset(skip).limit(limit).all()

def create_branch(db: Session, branch: schemas.BranchCreate):
    db_branch = models.Branch(name=branch.name, address=branch.address)
    db.add(db_branch)
    db.commit()
    db.refresh(db_branch)
    return db_branch

def update_branch(db: Session, branch_id: int, branch_update: schemas.BranchUpdate):
    db_branch = get_branch(db, branch_id)
    if not db_branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filial topilmadi")
    for key, value in branch_update.dict(exclude_unset=True).items():
        setattr(db_branch, key, value)
    db.commit()
    db.refresh(db_branch)
    return db_branch

def delete_branch(db: Session, branch_id: int):
    db_branch = get_branch(db, branch_id)
    if not db_branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filial topilmadi")
    db.delete(db_branch)
    db.commit()
    return {"ok": True}