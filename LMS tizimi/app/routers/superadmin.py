from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas, services, models  # models ni importlarga qo'shing
from ..core.database import get_db
from ..middlewares.auth_middleware import get_current_user, RoleChecker
router = APIRouter(prefix="/superadmin", tags=["SuperAdmin"])

allow_superadmin = RoleChecker(["SuperAdmin"]) # SuperAdmin role check

# Yangi adminlarni yaratish
@router.post("/admins/", response_model=schemas.UserSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(allow_superadmin)])
def create_admin(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = services.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email allaqachon ro'yxatdan o'tgan")
    # Admin role_id = 2 deb belgilaymiz (Role modelda aniqlangan bo'lishi kerak)
    user.role_id = 2
    return services.create_user(db=db, user=user)

# Barcha branchlardagi ma'lumotlarni ko'rish (misol uchun, barcha users)
@router.get("/users/", response_model=List[schemas.UserSchema], dependencies=[Depends(allow_superadmin)])
def read_all_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = services.get_users(db, skip=skip, limit=limit)
    return users

# Barcha teacherlar ro'yxatini ko'rish
@router.get("/teachers/", response_model=List[schemas.UserSchema], dependencies=[Depends(allow_superadmin)])
def read_all_teachers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # Teacher role_id = 3 deb belgilaymiz
    teachers = db.query(models.User).filter(models.User.role_id == 3).offset(skip).limit(limit).all()
    return teachers

# Barcha guruhlarni ko'rish
@router.get("/groups/", response_model=List[schemas.GroupSchema], dependencies=[Depends(allow_superadmin)])
def read_all_groups(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    groups = services.get_groups(db, skip=skip, limit=limit)
    return groups

# Barcha o'quvchilarni ko'rish
@router.get("/students/", response_model=List[schemas.StudentSchema], dependencies=[Depends(allow_superadmin)])
def read_all_students(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    students = services.get_students(db, skip=skip, limit=limit)
    return students

# Branchlarni boshqarish endpointlari (CRUD)
@router.post("/branches/", response_model=schemas.BranchSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(allow_superadmin)])
def create_branch(branch: schemas.BranchCreate, db: Session = Depends(get_db)):
    db_branch = services.get_branch_by_name(db, name=branch.name)
    if db_branch:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filial nomi allaqachon mavjud")
    return services.create_branch(db=db, branch=branch)

@router.get("/branches/", response_model=List[schemas.BranchSchema], dependencies=[Depends(allow_superadmin)])
def read_branches(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    branches = services.get_branches(db, skip=skip, limit=limit)
    return branches

@router.get("/branches/{branch_id}", response_model=schemas.BranchSchema, dependencies=[Depends(allow_superadmin)])
def read_branch(branch_id: int, db: Session = Depends(get_db)):
    db_branch = services.get_branch(db, branch_id=branch_id)
    if not db_branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filial topilmadi")
    return db_branch

@router.put("/branches/{branch_id}", response_model=schemas.BranchSchema, dependencies=[Depends(allow_superadmin)])
def update_branch(branch_id: int, branch_update: schemas.BranchUpdate, db: Session = Depends(get_db)):
    db_branch = services.get_branch(db, branch_id=branch_id)
    if not db_branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filial topilmadi")
    return services.update_branch(db=db, branch_id=branch_id, branch_update=branch_update)

@router.delete("/branches/{branch_id}", response_model=dict, dependencies=[Depends(allow_superadmin)])
def delete_branch(branch_id: int, db: Session = Depends(get_db)):
    db_branch = services.get_branch(db, branch_id=branch_id)
    if not db_branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filial topilmadi")
    return services.delete_branch(db=db, branch_id=branch_id)