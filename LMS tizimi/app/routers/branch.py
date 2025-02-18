from fastapi import APIRouter, Depends, HTTPException
from typing import List

from sqlalchemy.orm import Session

from .. import schemas, services
from ..core.database import get_db

router = APIRouter(prefix="/branches", tags=["Branches"])

@router.post("/", response_model=schemas.BranchSchema, status_code=201)
def create_branch(branch: schemas.BranchCreate, db: Session = Depends(get_db)):
    db_branch = services.get_branch_by_name(db, name=branch.name)
    if db_branch:
        raise HTTPException(status_code=400, detail="Filial nomi allaqachon mavjud")
    return services.create_branch(db=db, branch=branch)

@router.get("/{branch_id}", response_model=schemas.BranchSchema)
def read_branch(branch_id: int, db: Session = Depends(get_db)):
    db_branch = services.get_branch(db, branch_id=branch_id)
    if not db_branch:
        raise HTTPException(status_code=404, detail="Filial topilmadi")
    return db_branch

@router.get("/", response_model=List[schemas.BranchSchema])
def read_branches(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    branches = services.get_branches(db, skip=skip, limit=limit)
    return branches

@router.put("/{branch_id}", response_model=schemas.BranchSchema)
def update_branch(branch_id: int, branch_update: schemas.BranchUpdate, db: Session = Depends(get_db)):
    db_branch = services.get_branch(db, branch_id=branch_id)
    if not db_branch:
        raise HTTPException(status_code=404, detail="Filial topilmadi")
    return services.update_branch(db=db, branch_id=branch_id, branch_update=branch_update)

@router.delete("/{branch_id}", response_model=dict)
def delete_branch(branch_id: int, db: Session = Depends(get_db)):
    db_branch = services.get_branch(db, branch_id=branch_id)
    if not db_branch:
        raise HTTPException(status_code=404, detail="Filial topilmadi")
    return services.delete_branch(db=db, branch_id=branch_id)