from fastapi import APIRouter

from . import auth, superadmin, admin, teacher, student,branch,group

main_router = APIRouter()

main_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
main_router.include_router(superadmin.router, prefix="/superadmin", tags=["Superadmin"])
main_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
main_router.include_router(teacher.router, prefix="/teachers", tags=["Teachers"])
main_router.include_router(student.router, prefix="/students", tags=["Students"])
main_router.include_router(branch.router, prefix="/branches", tags=["Branches"])
main_router.include_router(group.router, prefix="/groups", tags=["Groups"])