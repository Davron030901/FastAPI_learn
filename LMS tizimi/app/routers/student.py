from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas, services, models
from ..core.database import get_db
from ..middlewares.auth_middleware import get_current_user, RoleChecker

router = APIRouter(prefix="/student", tags=["Student"])

allow_student_manage = RoleChecker(["Admin", "SuperAdmin"]) # Admin va SuperAdmin studentlarni boshqarishi mumkin

# Yangi o'quvchi qo'shish (Admin tomonidan)
@router.post("/", response_model=schemas.StudentSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(allow_student_manage)])
def create_student_in_branch(student: schemas.StudentCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role.name != "SuperAdmin" and student.branch_id != current_user.branch_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin faqat o'z filialida o'quvchi qo'sha oladi")
    db_student = services.get_student(db, student_id=student.email) # Email bilan tekshirish kerakmi? Uniqueness Emailga
    if db_student: # Email uniqueness tekshirish
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email allaqachon ro'yxatdan o'tgan")
    return services.create_student(db=db, student=student)

# O'quvchilarni ko'rish (Admin tomonidan)
@router.get("/", response_model=List[schemas.StudentSchema], dependencies=[Depends(allow_student_manage)])
def read_students(current_user: models.User = Depends(get_current_user), skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    if current_user.role.name == "SuperAdmin":
        students = services.get_students(db, skip=skip, limit=limit) # SuperAdmin hamma studentni ko'radi
    else:
        students = services.get_students_by_branch(db, branch_id=current_user.branch_id) # Admin o'z filialidagi studentlarni ko'radi
    return students

@router.get("/{student_id}", response_model=schemas.StudentSchema, dependencies=[Depends(allow_student_manage)])
def read_student(student_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_student = services.get_student(db, student_id=student_id)
    if not db_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="O'quvchi topilmadi")
    if current_user.role.name != "SuperAdmin" and db_student.branch_id != current_user.branch_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu o'quvchi sizning filialingizga tegishli emas")
    return db_student

@router.put("/{student_id}", response_model=schemas.StudentSchema, dependencies=[Depends(allow_student_manage)])
def update_student_in_branch(student_id: int, student_update: schemas.StudentUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_student = services.get_student(db, student_id=student_id)
    if not db_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="O'quvchi topilmadi")
    if current_user.role.name != "SuperAdmin" and db_student.branch_id != current_user.branch_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu o'quvchi sizning filialingizga tegishli emas")
    return services.update_student(db=db, student_id=student_id, student_update=student_update)

@router.delete("/{student_id}", response_model=dict, dependencies=[Depends(allow_student_manage)])
def delete_student_in_branch(student_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_student = services.get_student(db, student_id=student_id)
    if not db_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="O'quvchi topilmadi")
    if current_user.role.name != "SuperAdmin" and db_student.branch_id != current_user.branch_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu o'quvchi sizning filialingizga tegishli emas")
    return services.delete_student(db=db, student_id=student_id)

# O'quvchini guruhga qo'shish
@router.post("/groups/{group_id}/students/{student_id}", response_model=dict, dependencies=[Depends(allow_student_manage)])
def add_student_to_group_endpoint(group_id: int, student_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_group = services.get_group(db, group_id=group_id)
    db_student = services.get_student(db, student_id=student_id)
    if not db_group or not db_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guruh yoki o'quvchi topilmadi")
    if current_user.role.name != "SuperAdmin" and db_group.branch_id != current_user.branch_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu guruh sizning filialingizga tegishli emas")
    return services.add_student_to_group(db=db, group_id=group_id, student_id=student_id)

# O'quvchini guruhdan chiqarish
@router.delete("/groups/{group_id}/students/{student_id}", response_model=dict, dependencies=[Depends(allow_student_manage)])
def remove_student_from_group_endpoint(group_id: int, student_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_group = services.get_group(db, group_id=group_id)
    db_student = services.get_student(db, student_id=student_id)
    if not db_group or not db_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guruh yoki o'quvchi topilmadi")
    if current_user.role.name != "SuperAdmin" and db_group.branch_id != current_user.branch_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu guruh sizning filialingizga tegishli emas")
    return services.remove_student_from_group(db=db, group_id=group_id, student_id=student_id)