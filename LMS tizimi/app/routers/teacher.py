from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas, services, models
from ..core.database import get_db
from ..middlewares.auth_middleware import get_current_user, RoleChecker

router = APIRouter(prefix="/teacher", tags=["Teacher"])

allow_teacher = RoleChecker(["Teacher", "Admin", "SuperAdmin"]) # Teacher, Admin va SuperAdmin role check

# O'ziga biriktirilgan guruhlarni ko'rish
@router.get("/groups/", response_model=List[schemas.GroupSchema], dependencies=[Depends(allow_teacher)])
def read_teacher_groups(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return services.get_groups_by_teacher(db, teacher_id=current_user.id)

# O'z guruhlaridagi o'quvchilarni ko'rish
@router.get("/groups/{group_id}/students/", response_model=List[schemas.StudentSchema], dependencies=[Depends(allow_teacher)])
def read_group_students(group_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_group = services.get_group(db, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guruh topilmadi")
    if db_group.teacher_id != current_user.id: # Teacher faqat o'z guruhidagi o'quvchilarni ko'rishi mumkin
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu guruh sizga biriktirilmagan")
    return services.get_students_by_group(db, group_id=group_id)

# Guruhga oid ma'lumotlarni ko'rish (guruh nomi, filial, teacher, o'quvchilar soni va hokazo)
@router.get("/groups/{group_id}", response_model=schemas.GroupSchema, dependencies=[Depends(allow_teacher)])
def read_group_info(group_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_group = services.get_group(db, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guruh topilmadi")
    if db_group.teacher_id != current_user.id: # Teacher faqat o'z guruhining ma'lumotlarini ko'rishi mumkin
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu guruh sizga biriktirilmagan")
    return db_group