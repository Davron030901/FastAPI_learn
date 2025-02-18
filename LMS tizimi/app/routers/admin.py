from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas, services, models
from ..core.database import get_db
from ..middlewares.auth_middleware import get_current_user, RoleChecker

router = APIRouter(prefix="/admin", tags=["Admin"])

allow_admin = RoleChecker(["Admin", "SuperAdmin"]) # Admin va SuperAdmin role check

# O'z branchidagi teacherlarni qo'shish
@router.post("/teachers/", response_model=schemas.UserSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(allow_admin)])
def create_teacher_in_branch(user: schemas.UserCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role.name != "SuperAdmin" and user.branch_id != current_user.branch_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin faqat o'z filialida teacher qo'sha oladi")
    db_user = services.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email allaqachon ro'yxatdan o'tgan")
    # Teacher role_id = 3 deb belgilaymiz
    user.role_id = 3
    return services.create_user(db=db, user=user)

# O'z branchidagi teacherlarni ko'rish
@router.get("/teachers/", response_model=List[schemas.UserSchema], dependencies=[Depends(allow_admin)])
def read_branch_teachers(current_user: models.User = Depends(get_current_user), skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    if current_user.role.name == "SuperAdmin":
        teachers = db.query(models.User).filter(models.User.role_id == 3).offset(skip).limit(limit).all() # SuperAdmin hamma teacherni ko'radi
    else:
        teachers = services.get_teachers_by_branch(db, branch_id=current_user.branch_id, ) # Admin o'z filialidagi teacherlarni ko'radi
    return teachers

# O'z branchidagi o'quvchilarni ko'rish
@router.get("/students/", response_model=List[schemas.StudentSchema], dependencies=[Depends(allow_admin)])
def read_branch_students(current_user: models.User = Depends(get_current_user), skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    if current_user.role.name == "SuperAdmin":
        students = services.get_students(db, skip=skip, limit=limit) # SuperAdmin hamma studentni ko'radi
    else:
        students = services.get_students_by_branch(db, branch_id=current_user.branch_id) # Admin o'z filialidagi studentlarni ko'radi
    return students

# O'z branchidagi guruhlarni boshqarish (ko'rish, yaratish, yangilash, o'chirish)
@router.post("/groups/", response_model=schemas.GroupSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(allow_admin)])
def create_group_in_branch(group: schemas.GroupCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role.name != "SuperAdmin" and group.branch_id != current_user.branch_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin faqat o'z filialida guruh yarata oladi")
    return services.create_group(db=db, group=group)

@router.get("/groups/", response_model=List[schemas.GroupSchema], dependencies=[Depends(allow_admin)])
def read_branch_groups(current_user: models.User = Depends(get_current_user), skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    if current_user.role.name == "SuperAdmin":
        groups = services.get_groups(db, skip=skip, limit=limit) # SuperAdmin hamma guruhni ko'radi
    else:
        groups = services.get_groups_by_branch(db, branch_id=current_user.branch_id) # Admin o'z filialidagi guruhlarni ko'radi
    return groups

@router.get("/groups/{group_id}", response_model=schemas.GroupSchema, dependencies=[Depends(allow_admin)])
def read_branch_group(group_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_group = services.get_group(db, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guruh topilmadi")
    if current_user.role.name != "SuperAdmin" and db_group.branch_id != current_user.branch_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu guruh sizning filialingizga tegishli emas")
    return db_group

@router.put("/groups/{group_id}", response_model=schemas.GroupSchema, dependencies=[Depends(allow_admin)])
def update_group_in_branch(group_id: int, group_update: schemas.GroupUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_group = services.get_group(db, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guruh topilmadi")
    if current_user.role.name != "SuperAdmin" and db_group.branch_id != current_user.branch_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu guruh sizning filialingizga tegishli emas")
    return services.update_group(db=db, group_id=group_id, group_update=group_update)

@router.delete("/groups/{group_id}", response_model=dict, dependencies=[Depends(allow_admin)])
def delete_group_in_branch(group_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_group = services.get_group(db, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guruh topilmadi")
    if current_user.role.name != "SuperAdmin" and db_group.branch_id != current_user.branch_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu guruh sizning filialingizga tegishli emas")
    return services.delete_group(db=db, group_id=group_id)

# Guruhlarga teacher biriktirish
@router.put("/groups/{group_id}/teacher/{teacher_id}", response_model=schemas.GroupSchema, dependencies=[Depends(allow_admin)])
def assign_teacher_to_group(group_id: int, teacher_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_group = services.get_group(db, group_id=group_id)
    db_teacher = services.get_user(db, teacher_id=teacher_id) # User modelidan teacher olish
    if not db_group or not db_teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guruh yoki teacher topilmadi")
    if current_user.role.name != "SuperAdmin" and db_group.branch_id != current_user.branch_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu guruh sizning filialingizga tegishli emas")
    if db_teacher.role.name != "Teacher":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Berilgan user teacher emas")
    db_group.teacher_id = teacher_id
    db.commit()
    db.refresh(db_group)
    return db_group