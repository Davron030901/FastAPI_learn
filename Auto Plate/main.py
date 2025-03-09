# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, DateTime, Float, UniqueConstraint, func, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from typing import List, Optional
from pydantic import BaseModel, validator, Field
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import re
import uvicorn
from enum import Enum
from fastapi.middleware.cors import CORSMiddleware

# Configuration
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database settings
SQLALCHEMY_DATABASE_URL = "sqlite:///./auto_plate_bidding.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI(title="Auto Plate Bidding API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],  # Vite's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Region and letter enums
class Region(str, Enum):
    R01 = "01"
    R10 = "10"
    R20 = "20"
    R25 = "25"
    R30 = "30"
    R40 = "40"
    R50 = "50"
    R60 = "60"
    R70 = "70"
    R75 = "75"
    R80 = "80"
    R85 = "85"
    R90 = "90"
    R95 = "95"

class Letter(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    J = "J"
    K = "K"
    L = "L"
    M = "M"
    N = "N"
    O = "O"
    P = "P"
    Q = "Q"
    R = "R"
    S = "S"
    T = "T"
    U = "U"
    V = "V"
    W = "W"
    X = "X"
    Y = "Y"
    Z = "Z"

# Database models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_staff = Column(Boolean, default=False)
    
    plates_created = relationship("AutoPlate", back_populates="created_by")
    bids = relationship("Bid", back_populates="user")

class AutoPlate(Base):
    __tablename__ = "auto_plates"
    
    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String(10), unique=True, index=True)
    description = Column(String)
    deadline = Column(DateTime)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    
    created_by = relationship("User", back_populates="plates_created")
    bids = relationship("Bid", back_populates="plate", cascade="all, delete-orphan")

class Bid(Base):
    __tablename__ = "bids"
    
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    user_id = Column(Integer, ForeignKey("users.id"))
    plate_id = Column(Integer, ForeignKey("auto_plates.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="bids")
    plate = relationship("AutoPlate", back_populates="bids")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'plate_id', name='unique_user_plate'),
    )

# Create database tables
Base.metadata.create_all(bind=engine)

# Pydantic models (Serializers)
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str
    is_staff: bool = False

class UserResponse(UserBase):
    id: int
    is_staff: bool
    
    class Config:
        from_attributes = True

class PlateBase(BaseModel):
    plate_number: str
    description: str
    deadline: datetime
    
    @validator('plate_number')
    def validate_plate_number(cls, v):
        # Pattern for "R L NNN LL" format
        pattern = r'^(01|10|20|25|30|40|50|60|70|75|80|85|90|95)[A-HJ-Z][0-9]{3}[A-HJ-Z]{2}$'
        if not re.match(pattern, v):
            raise ValueError("Incorrect auto plate format. Format: R L NNN LL (R - region, L - letter, N - number)")
        return v
    
    @validator('deadline')
    def validate_deadline(cls, v):
        if v <= datetime.utcnow():
            raise ValueError("Deadline must be in the future")
        return v

class PlateCreate(PlateBase):
    pass

class BidBase(BaseModel):
    amount: float
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Bid amount must be positive")
        return v

class BidCreate(BidBase):
    plate_id: int

class BidUpdate(BidBase):
    pass

class BidResponse(BidBase):
    id: int
    plate_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class BidDetailResponse(BidResponse):
    user_id: int
    
    class Config:
        from_attributes = True

class PlateResponse(PlateBase):
    id: int
    is_active: bool
    highest_bid: Optional[float] = None
    
    class Config:
        from_attributes = True

class PlateDetailResponse(PlateResponse):
    bids: List[BidDetailResponse] = []
    
    class Config:
        from_attributes = True

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user

def is_admin(user: User):
    if not user.is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return True

# API endpoints
@app.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_staff=user.is_staff
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# AutoPlate endpoints
@app.get("/plates", response_model=List[PlateResponse])
def list_plates(
    ordering: Optional[str] = None,
    plate_number_contains: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AutoPlate)
    
    if plate_number_contains:
        query = query.filter(AutoPlate.plate_number.contains(plate_number_contains))
    
    if ordering == "deadline":
        query = query.order_by(AutoPlate.deadline)
    elif ordering == "-deadline":
        query = query.order_by(desc(AutoPlate.deadline))
    
    plates = query.all()
    
    # Calculate highest bid for each plate
    result = []
    for plate in plates:
        highest_bid = None
        if plate.bids:
            highest_bid = max([bid.amount for bid in plate.bids], default=None)
        
        plate_data = PlateResponse(
            id=plate.id,
            plate_number=plate.plate_number,
            description=plate.description,
            deadline=plate.deadline,
            is_active=plate.is_active,
            highest_bid=highest_bid
        )
        result.append(plate_data)
    
    return result

@app.post("/plates", response_model=PlateResponse)
def create_plate(
    plate: PlateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Check admin rights
    is_admin(current_user)
    
    # Check plate number uniqueness
    existing_plate = db.query(AutoPlate).filter(AutoPlate.plate_number == plate.plate_number).first()
    if existing_plate:
        raise HTTPException(status_code=400, detail="Plate number already exists")
    
    # Create new plate
    db_plate = AutoPlate(
        plate_number=plate.plate_number,
        description=plate.description,
        deadline=plate.deadline,
        created_by_id=current_user.id,
        is_active=True
    )
    db.add(db_plate)
    db.commit()
    db.refresh(db_plate)
    
    return PlateResponse(
        id=db_plate.id,
        plate_number=db_plate.plate_number,
        description=db_plate.description,
        deadline=db_plate.deadline,
        is_active=db_plate.is_active,
        highest_bid=None
    )

@app.get("/plates/{plate_id}", response_model=PlateDetailResponse)
def get_plate(plate_id: int, db: Session = Depends(get_db)):
    plate = db.query(AutoPlate).filter(AutoPlate.id == plate_id).first()
    if not plate:
        raise HTTPException(status_code=404, detail="Plate not found")
    
    # Return plate details with bids
    bid_responses = []
    highest_bid = None
    
    for bid in plate.bids:
        bid_detail = BidDetailResponse(
            id=bid.id,
            amount=bid.amount,
            plate_id=bid.plate_id,
            created_at=bid.created_at,
            user_id=bid.user_id
        )
        bid_responses.append(bid_detail)
        
        # Find highest bid
        if highest_bid is None or bid.amount > highest_bid:
            highest_bid = bid.amount
    
    return PlateDetailResponse(
        id=plate.id,
        plate_number=plate.plate_number,
        description=plate.description,
        deadline=plate.deadline,
        is_active=plate.is_active,
        highest_bid=highest_bid,
        bids=bid_responses
    )

@app.put("/plates/{plate_id}", response_model=PlateResponse)
def update_plate(
    plate_id: int,
    plate_update: PlateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Check admin rights
    is_admin(current_user)
    
    # Find plate
    db_plate = db.query(AutoPlate).filter(AutoPlate.id == plate_id).first()
    if not db_plate:
        raise HTTPException(status_code=404, detail="Plate not found")
    
    # Check plate number uniqueness
    if db_plate.plate_number != plate_update.plate_number:
        existing_plate = db.query(AutoPlate).filter(AutoPlate.plate_number == plate_update.plate_number).first()
        if existing_plate:
            raise HTTPException(status_code=400, detail="Plate number already exists")
    
    # Update plate
    db_plate.plate_number = plate_update.plate_number
    db_plate.description = plate_update.description
    db_plate.deadline = plate_update.deadline
    
    db.commit()
    db.refresh(db_plate)
    
    # Find highest bid
    highest_bid = None
    if db_plate.bids:
        highest_bid = max([bid.amount for bid in db_plate.bids], default=None)
    
    return PlateResponse(
        id=db_plate.id,
        plate_number=db_plate.plate_number,
        description=db_plate.description,
        deadline=db_plate.deadline,
        is_active=db_plate.is_active,
        highest_bid=highest_bid
    )

@app.delete("/plates/{plate_id}", status_code=204)
def delete_plate(
    plate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Check admin rights
    is_admin(current_user)
    
    # Find plate
    db_plate = db.query(AutoPlate).filter(AutoPlate.id == plate_id).first()
    if not db_plate:
        raise HTTPException(status_code=404, detail="Plate not found")
    
    # Delete plate (cascade will delete related bids)
    db.delete(db_plate)
    db.commit()
    
    return {"detail": "Plate successfully deleted"}

# Bid endpoints
@app.get("/bids", response_model=List[BidResponse])
def list_bids(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Return only user's own bids
    bids = db.query(Bid).filter(Bid.user_id == current_user.id).all()
    return bids

@app.post("/bids", response_model=BidResponse)
def create_bid(
    bid: BidCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Check plate
    plate = db.query(AutoPlate).filter(AutoPlate.id == bid.plate_id).first()
    if not plate:
        raise HTTPException(status_code=404, detail="Plate not found")
    
    # Check if bidding is active
    if not plate.is_active or plate.deadline <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="Bidding is closed")
    
    # Check if user already has a bid on this plate
    existing_bid = db.query(Bid).filter(
        Bid.user_id == current_user.id,
        Bid.plate_id == bid.plate_id
    ).first()
    
    if existing_bid:
        raise HTTPException(status_code=400, detail="You already have a bid on this plate")
    
    # Check highest bid
    highest_bid = db.query(func.max(Bid.amount)).filter(Bid.plate_id == bid.plate_id).scalar()
    if highest_bid and bid.amount <= highest_bid:
        raise HTTPException(status_code=400, detail="Bid must exceed current highest bid")
    
    # Create new bid
    db_bid = Bid(
        amount=bid.amount,
        user_id=current_user.id,
        plate_id=bid.plate_id,
        created_at=datetime.utcnow()
    )
    db.add(db_bid)
    db.commit()
    db.refresh(db_bid)
    
    return BidResponse(
        id=db_bid.id,
        amount=db_bid.amount,
        plate_id=db_bid.plate_id,
        created_at=db_bid.created_at
    )

@app.get("/bids/{bid_id}", response_model=BidResponse)
def get_bid(
    bid_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Find bid
    bid = db.query(Bid).filter(Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Only allow viewing own bids
    if bid.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this bid")
    
    return bid

@app.put("/bids/{bid_id}", response_model=BidResponse)
def update_bid(
    bid_id: int,
    bid_update: BidUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Find bid
    db_bid = db.query(Bid).filter(Bid.id == bid_id).first()
    if not db_bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Only allow updating own bids
    if db_bid.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this bid")
    
    # Check bidding deadline
    plate = db.query(AutoPlate).filter(AutoPlate.id == db_bid.plate_id).first()
    if plate.deadline <= datetime.utcnow():
        raise HTTPException(status_code=403, detail="Bidding period has ended")
    
    # Check highest bid
    highest_bid = db.query(func.max(Bid.amount)).filter(
        Bid.plate_id == db_bid.plate_id,
        Bid.id != bid_id
    ).scalar()
    
    if highest_bid and bid_update.amount <= highest_bid:
        raise HTTPException(status_code=400, detail="Bid must exceed current highest bid")
    
    # Update bid
    db_bid.amount = bid_update.amount
    db.commit()
    db.refresh(db_bid)
    
    return db_bid

@app.delete("/bids/{bid_id}", status_code=204)
def delete_bid(
    bid_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Find bid
    db_bid = db.query(Bid).filter(Bid.id == bid_id).first()
    if not db_bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Only allow deleting own bids
    if db_bid.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this bid")
    
    # Check bidding deadline
    plate = db.query(AutoPlate).filter(AutoPlate.id == db_bid.plate_id).first()
    if plate.deadline <= datetime.utcnow():
        raise HTTPException(status_code=403, detail="Bidding period has ended")
    
    # Delete bid
    db.delete(db_bid)
    db.commit()
    
    return {"detail": "Bid successfully deleted"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)