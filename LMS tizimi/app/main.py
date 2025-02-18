from fastapi import FastAPI
from .core.database import engine, Base
from .routers import main_router # main_router ni __init__.py dan import qiling

Base.metadata.create_all(bind=engine) # Database modellarni yaratish

app = FastAPI(title="Ta'lim Tizimi API", description="Multi-tenancy asosidagi ta'lim tizimi API")

app.include_router(main_router)