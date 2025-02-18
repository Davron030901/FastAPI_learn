from sqlalchemy.orm import Session
from .. import models, schemas  # Import models va schemas parent papkadan

def get_teacher(db: Session, teacher_id: int):
    return db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()

def get_teacher_by_email(db: Session, email: str):
    return db.query(models.Teacher).filter(models.Teacher.email == email).first()

def get_teachers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Teacher).offset(skip).limit(limit).all()

def create_teacher(db: Session, teacher: schemas.TeacherCreate):
    db_teacher = models.Teacher(**teacher.dict()) # Pydantic schemani modelga o'tkazamiz
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher

def update_teacher(db: Session, teacher_id: int, teacher_update: schemas.TeacherUpdate):
    db_teacher = get_teacher(db, teacher_id)
    if not db_teacher:
        return None
    for key, value in teacher_update.dict(exclude_unset=True).items():
        setattr(db_teacher, key, value)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher

def delete_teacher(db: Session, teacher_id: int):
    db_teacher = get_teacher(db, teacher_id)
    if not db_teacher:
        return None
    db.delete(db_teacher)
    db.commit()
    return db_teacher