from database import engine
import models

def create_tables():
    try:
        models.Base.metadata.create_all(bind=engine)
        print("Jadvallar muvaffaqiyatli yaratildi!")
    except Exception as e:
        print(f"Jadvallarni yaratishda xatolik: {e}")

if __name__ == "__main__":
    create_tables()