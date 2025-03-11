from sqlalchemy import text
from database import SessionLocal, engine
import models
from datetime import datetime, timedelta
import random
from decimal import Decimal
from passlib.context import CryptContext
import bcrypt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Passwordni hash qilish"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def clear_database():
    """Mavjud ma'lumotlarni o'chirish"""
    db = SessionLocal()
    try:
        # Foreign key constraintlarni vaqtincha o'chirish
        db.execute(text("PRAGMA foreign_keys=OFF"))
        
        # Barcha jadvallarni tozalash
        db.execute(text("DELETE FROM bids"))
        db.execute(text("DELETE FROM auto_plates"))
        db.execute(text("DELETE FROM users"))
        
        # Auto-increment counterlarni qayta boshlash
        db.execute(text("DELETE FROM sqlite_sequence"))
        
        # Foreign key constraintlarni yoqish
        db.execute(text("PRAGMA foreign_keys=ON"))
        
        db.commit()
        print("Database tozalandi")
    except Exception as e:
        print(f"Databaseni tozalashda xatolik: {e}")
        db.rollback()
    finally:
        db.close()

def seed_database():
    # Create all tables first
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Clear existing data safely
        db.execute(text("PRAGMA foreign_keys=OFF"))
        
        # Clear tables if they exist
        try:
            db.execute(text("DELETE FROM bids"))
            db.execute(text("DELETE FROM auto_plates"))
            db.execute(text("DELETE FROM users"))
        except Exception:
            pass  # Tables might not exist yet
        
        db.execute(text("PRAGMA foreign_keys=ON"))
        db.commit()
        
        # Create admin user
        admin_password = pwd_context.hash("admin")
        admin = models.User(
            username="admin",
            email="admin@example.com",
            password=admin_password,
            is_staff=True
        )
        db.add(admin)
        
        # Create test users
        test_users = [
            ("user1", "user1@example.com", "user123"),
            ("user2", "user2@example.com", "user123"),
            ("user3", "user3@example.com", "user123")
        ]
        
        users = []
        for username, email, password in test_users:
            hashed_password = pwd_context.hash(password)
            user = models.User(
                username=username,
                email=email,
                password=hashed_password,
                is_staff=False
            )
            db.add(user)
            users.append(user)
        
        db.flush()
        
        # Create plates
        plates = []
        plate_numbers = [
            "01A777AA", "01A999BB", "01A555CC",
            "01A333DD", "01A111EE", "01A888FF"
        ]
        
        for number in plate_numbers:
            deadline = datetime.now() + timedelta(days=random.randint(1, 30))
            plate = models.AutoPlate(
                plate_number=number,
                description=f"Premium avto raqam {number}",
                deadline=deadline,
                starting_price=Decimal(str(random.randint(1000, 5000))),
                created_by_id=admin.id,
                is_active=True
            )
            db.add(plate)
            plates.append(plate)
        
        db.flush()
        
        # Create bids
        for plate in plates:
            base_amount = plate.starting_price
            for i in range(random.randint(1, 3)):
                user = random.choice(users)
                amount = float(base_amount) + (i + 1) * random.randint(100, 1000)
                
                bid = models.Bid(
                    amount=Decimal(str(amount)),
                    user_id=user.id,
                    plate_id=plate.id,
                    created_at=datetime.now() - timedelta(hours=random.randint(1, 24))
                )
                db.add(bid)
        
        db.commit()
        print("Database muvaffaqiyatli to'ldirildi!")
        
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()