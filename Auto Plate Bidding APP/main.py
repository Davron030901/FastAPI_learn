# main.py
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal  # Add this import
import jwt
import uvicorn
import json
from pathlib import Path
import asyncio

# Import database models and schemas
from database import SessionLocal, engine
import models
import schemas
from passlib.context import CryptContext

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Avto Raqamlar Auktsioni")

# Set up static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Authentication settings
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, plate_id: int):
        await websocket.accept()
        if plate_id not in self.active_connections:
            self.active_connections[plate_id] = []
        self.active_connections[plate_id].append(websocket)

    def disconnect(self, websocket: WebSocket, plate_id: int):
        if plate_id in self.active_connections:
            if websocket in self.active_connections[plate_id]:
                self.active_connections[plate_id].remove(websocket)
            if not self.active_connections[plate_id]:
                del self.active_connections[plate_id]

    async def broadcast(self, message: str, plate_id: int):
        if plate_id in self.active_connections:
            for connection in self.active_connections[plate_id]:
                await connection.send_text(message)

manager = ConnectionManager()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> models.User:
    try:
        token = request.cookies.get("token")
        if not token or not token.startswith("Bearer "):
            return None
            
        token = token.split("Bearer ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            return None
            
        user = get_user_by_username(db, username)
        return user
    except:
        return None

# User registration
@app.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        password=hashed_password,
        is_staff=user.is_staff if hasattr(user, 'is_staff') else False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Login endpoint
@app.post("/login", response_model=schemas.Token)
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

# Auto Plate Endpoints
@app.get("/plates/", response_model=List[schemas.AutoPlateWithHighestBid])
def list_plates(
    ordering: Optional[str] = None,
    plate_number__contains: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Base query
    query = db.query(models.AutoPlate).filter(models.AutoPlate.is_active == True)
    
    # Filter by plate number if provided
    if plate_number__contains:
        query = query.filter(models.AutoPlate.plate_number.ilike(f"%{plate_number__contains}%"))
    
    # Apply ordering
    if ordering:
        if ordering == "deadline":
            query = query.order_by(models.AutoPlate.deadline.asc())
        elif ordering == "-deadline":
            query = query.order_by(models.AutoPlate.deadline.desc())
    else:
        # Default ordering by deadline ascending
        query = query.order_by(models.AutoPlate.deadline.asc())
    
    # Execute query
    plates = query.all()
    result = []
    
    # Add highest bids
    for plate in plates:
        highest_bid = db.query(models.Bid).filter(
            models.Bid.plate_id == plate.id
        ).order_by(models.Bid.amount.desc()).first()
        
        plate_with_bid = schemas.AutoPlateWithHighestBid(
            id=plate.id,
            plate_number=plate.plate_number,
            description=plate.description,
            deadline=plate.deadline,
            is_active=plate.is_active,
            highest_bid=highest_bid.amount if highest_bid else None
        )
        result.append(plate_with_bid)
    
    return result

@app.post("/plates/", response_model=schemas.AutoPlateResponse, status_code=201)
def create_plate(
    plate: schemas.AutoPlateCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized to create plates")
    
    # Check if deadline is in the future
    if plate.deadline <= datetime.now():
        raise HTTPException(status_code=400, detail="Deadline must be in the future")
    
    # Check if plate number is unique
    existing_plate = db.query(models.AutoPlate).filter(
        models.AutoPlate.plate_number == plate.plate_number
    ).first()
    
    if existing_plate:
        raise HTTPException(status_code=400, detail="Plate number already exists")
    
    db_plate = models.AutoPlate(
        plate_number=plate.plate_number,
        description=plate.description,
        deadline=plate.deadline,
        created_by_id=current_user.id,
        is_active=True
    )
    
    db.add(db_plate)
    try:
        db.commit()
        db.refresh(db_plate)
        return db_plate
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error creating plate")

@app.get("/plates/{plate_id}", response_model=schemas.AutoPlateWithBids)
def get_plate(plate_id: int, db: Session = Depends(get_db)):
    plate = db.query(models.AutoPlate).filter(models.AutoPlate.id == plate_id).first()
    if not plate:
        raise HTTPException(status_code=404, detail="Plate not found")
    
    bids = db.query(models.Bid).filter(models.Bid.plate_id == plate_id).all()
    
    return {
        "id": plate.id,
        "plate_number": plate.plate_number,
        "description": plate.description,
        "deadline": plate.deadline,
        "is_active": plate.is_active,
        "bids": bids
    }

def update_plate(
    plate_id: int,
    plate_update: schemas.AutoPlateUpdate,
    current_user: models.User,
    db: Session
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized to update plates")
    
    db_plate = db.query(models.AutoPlate).filter(models.AutoPlate.id == plate_id).first()
    if not db_plate:
        raise HTTPException(status_code=404, detail="Plate not found")
    
    # Update plate fields
    db_plate.plate_number = plate_update.plate_number
    db_plate.description = plate_update.description
    db_plate.deadline = plate_update.deadline
    db_plate.is_active = plate_update.is_active
    
    try:
        db.commit()
        
        # Create update message
        update_message = {
            "type": "plate_update",
            "plate_id": db_plate.id,
            "plate_number": db_plate.plate_number,
            "description": db_plate.description,
            "deadline": db_plate.deadline.isoformat(),
            "is_active": db_plate.is_active
        }
        
        # Pass plate_id to broadcast
        asyncio.create_task(manager.broadcast(json.dumps(update_message), db_plate.id))
        
        return db_plate
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/plates/{plate_id}", status_code=204)
def delete_plate(
    plate_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized to delete plates")
    
    db_plate = db.query(models.AutoPlate).filter(models.AutoPlate.id == plate_id).first()
    if not db_plate:
        raise HTTPException(status_code=404, detail="Plate not found")
    
    # Check if plate has bids
    bids_count = db.query(models.Bid).filter(models.Bid.plate_id == plate_id).count()
    if bids_count > 0:
        raise HTTPException(status_code=400, detail="Cannot delete plate with active bids")
    
    db.delete(db_plate)
    db.commit()
    
    return None

# Bid Endpoints
@app.get("/bids/", response_model=List[schemas.BidResponse])
def list_user_bids(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bids = db.query(models.Bid).filter(models.Bid.user_id == current_user.id).all()
    return bids

@app.post("/bids/", response_model=schemas.BidResponse, status_code=201)
async def create_bid(
    bid: schemas.BidCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if amount is positive
    if bid.amount <= 0:
        raise HTTPException(status_code=400, detail="Bid amount must be positive")
    
    # Check if plate exists and is active
    plate = db.query(models.AutoPlate).filter(models.AutoPlate.id == bid.plate_id).first()
    if not plate:
        raise HTTPException(status_code=404, detail="Plate not found")
    
    if not plate.is_active:
        raise HTTPException(status_code=400, detail="Auction is closed")
    
    if plate.deadline <= datetime.now():
        raise HTTPException(status_code=400, detail="Auction has ended")
    
    # Check if user already has a bid for this plate
    existing_bid = db.query(models.Bid).filter(
        models.Bid.plate_id == bid.plate_id,
        models.Bid.user_id == current_user.id
    ).first()
    
    # Find the highest current bid
    highest_bid = db.query(models.Bid).filter(
        models.Bid.plate_id == bid.plate_id
    ).order_by(models.Bid.amount.desc()).first()
    
    # Check if bid is higher than current highest
    if highest_bid and bid.amount <= highest_bid.amount:
        raise HTTPException(
            status_code=400, 
            detail=f"Bid must be higher than the current highest bid of {highest_bid.amount}"
        )
    
    if existing_bid:
        # Update existing bid if user already bid
        existing_bid.amount = bid.amount
        existing_bid.created_at = datetime.now()
        db.commit()
        db.refresh(existing_bid)
        new_bid = existing_bid
    else:
        # Create new bid
        new_bid = models.Bid(
            amount=bid.amount,
            user_id=current_user.id,
            plate_id=bid.plate_id,
            created_at=datetime.now()
        )
        db.add(new_bid)
        db.commit()
        db.refresh(new_bid)
    
    # Notify all connected WebSocket clients about the new bid
    bid_update = {
        "action": "new_bid",
        "plate_id": new_bid.plate_id,
        "bid_amount": float(new_bid.amount),
        "bidder_id": new_bid.user_id,
        "bidder_username": current_user.username,
        "timestamp": new_bid.created_at.isoformat()
    }
    
    await manager.broadcast(json.dumps(bid_update), new_bid.plate_id)
    
    return new_bid

@app.get("/bids/{bid_id}", response_model=schemas.BidResponse)
def get_bid(
    bid_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bid = db.query(models.Bid).filter(models.Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    if bid.user_id != current_user.id and not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized to view this bid")
    
    return bid

@app.put("/bids/{bid_id}", response_model=schemas.BidResponse)
async def update_bid(
    bid_id: int,
    bid_update: schemas.BidUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bid = db.query(models.Bid).filter(models.Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    if bid.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this bid")
    
    plate = db.query(models.AutoPlate).filter(models.AutoPlate.id == bid.plate_id).first()
    if plate.deadline <= datetime.now():
        raise HTTPException(status_code=403, detail="Auction period has ended")
    
    # Check if amount is positive
    if bid_update.amount <= 0:
        raise HTTPException(status_code=400, detail="Bid amount must be positive")
    
    # Find the highest current bid
    highest_bid = db.query(models.Bid).filter(
        models.Bid.plate_id == bid.plate_id
    ).order_by(models.Bid.amount.desc()).first()
    
    # Check if bid is higher than current highest (if not the user's own bid)
    if highest_bid and highest_bid.id != bid.id and bid_update.amount <= highest_bid.amount:
        raise HTTPException(
            status_code=400, 
            detail=f"Bid must be higher than the current highest bid of {highest_bid.amount}"
        )
    
    bid.amount = bid_update.amount
    db.commit()
    db.refresh(bid)
    
    # Notify all connected WebSocket clients about the updated bid
    bid_update_message = {
        "action": "bid_updated",
        "plate_id": bid.plate_id,
        "bid_id": bid.id,
        "bid_amount": float(bid.amount),
        "bidder_id": bid.user_id,
        "bidder_username": current_user.username,
        "timestamp": datetime.now().isoformat()
    }
    
    await manager.broadcast(json.dumps(bid_update_message), bid.plate_id)
    
    return bid

@app.delete("/bids/{bid_id}", status_code=204)
async def delete_bid(
    bid_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bid = db.query(models.Bid).filter(models.Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    if bid.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this bid")
    
    plate = db.query(models.AutoPlate).filter(models.AutoPlate.id == bid.plate_id).first()
    if plate.deadline <= datetime.now():
        raise HTTPException(status_code=403, detail="Auction period has ended")
    
    plate_id = bid.plate_id
    db.delete(bid)
    db.commit()
    
    # Notify all connected WebSocket clients about the deleted bid
    bid_delete_message = {
        "action": "bid_deleted",
        "plate_id": plate_id,
        "bid_id": bid_id,
        "bidder_id": current_user.id,
        "bidder_username": current_user.username,
        "timestamp": datetime.now().isoformat()
    }
    
    await manager.broadcast(json.dumps(bid_delete_message), plate_id)
    
    return None

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{plate_id}")
async def websocket_endpoint(websocket: WebSocket, plate_id: int, db: Session = Depends(get_db)):
    plate = db.query(models.AutoPlate).filter(models.AutoPlate.id == plate_id).first()
    if not plate:
        await websocket.close(code=1008, reason="Plate not found")
        return
    
    await manager.connect(websocket, plate_id)
    try:
        while True:
            # Just keep the connection alive, we'll broadcast from the bid endpoints
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, plate_id)

# Web UI Routes
@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    ordering: Optional[str] = None,
    plate_number__contains: Optional[str] = None,
    current_user: Optional[models.User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Base query
    query = db.query(models.AutoPlate).filter(models.AutoPlate.is_active == True)
    
    # Filter by plate number if provided
    if plate_number__contains:
        query = query.filter(models.AutoPlate.plate_number.ilike(f"%{plate_number__contains}%"))
    
    # Apply ordering
    if ordering:
        if ordering == "deadline":
            query = query.order_by(models.AutoPlate.deadline.asc())
        elif ordering == "-deadline":
            query = query.order_by(models.AutoPlate.deadline.desc())
    else:
        query = query.order_by(models.AutoPlate.deadline.asc())
    
    plates = query.all()
    
    # Add highest bids
    result = []
    for plate in plates:
        highest_bid = db.query(models.Bid).filter(
            models.Bid.plate_id == plate.id
        ).order_by(models.Bid.amount.desc()).first()
        
        result.append({
            "id": plate.id,
            "plate_number": plate.plate_number,
            "description": plate.description,
            "deadline": plate.deadline,
            "is_active": plate.is_active,
            "highest_bid": highest_bid.amount if highest_bid else None
        })
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": current_user,
            "plates": result,
        }
    )

@app.get("/login-page", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register-page", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/plate/{plate_id}", response_class=HTMLResponse)
async def plate_detail(request: Request, plate_id: int, db: Session = Depends(get_db)):
    plate = db.query(models.AutoPlate).filter(models.AutoPlate.id == plate_id).first()
    if not plate:
        raise HTTPException(status_code=404, detail="Plate not found")
    
    bids = db.query(models.Bid).filter(models.Bid.plate_id == plate_id).order_by(models.Bid.amount.desc()).all()
    
    highest_bid = bids[0].amount if bids else 0
    
    return templates.TemplateResponse(
        "plate_detail.html", 
        {
            "request": request, 
            "plate": plate, 
            "bids": bids,
            "highest_bid": highest_bid
        }
    )

@app.get("/admin/plates", response_class=HTMLResponse)
async def admin_plates(
    request: Request, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized to access admin area")
    
    plates = db.query(models.AutoPlate).all()
    return templates.TemplateResponse(
        "admin_plates.html", 
        {"request": request, "plates": plates, "user": current_user}
    )

@app.get("/admin/plate/new", response_class=HTMLResponse)
async def admin_new_plate(
    request: Request,
    current_user: models.User = Depends(get_current_user)
):
    try:
        if not current_user.is_staff:
            return RedirectResponse(
                url="/login-page?next=/admin/plate/new",
                status_code=status.HTTP_302_FOUND
            )
        
        return templates.TemplateResponse(
            "admin_plate_form.html",
            {
                "request": request,
                "user": current_user,
                "now": datetime.now()
            }
        )
    except HTTPException:
        return RedirectResponse(
            url="/login-page?next=/admin/plate/new",
            status_code=status.HTTP_302_FOUND
        )

@app.get("/admin/plate/{plate_id}/edit", response_class=HTMLResponse)
async def admin_edit_plate(
    request: Request, 
    plate_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized to access admin area")
    
    plate = db.query(models.AutoPlate).filter(models.AutoPlate.id == plate_id).first()
    if not plate:
        raise HTTPException(status_code=404, detail="Plate not found")
    
    return templates.TemplateResponse(
        "admin_plate_form.html", 
        {
            "request": request, 
            "user": current_user, 
            "plate": plate,
            "now": datetime.now()  # Add this line
        }
    )

@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users(
    request: Request, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Adminlik huquqi yo'q")
    
    users = db.query(models.User).all()
    return templates.TemplateResponse(
        "admin_users.html", 
        {"request": request, "users": users, "user": current_user}
    )

@app.get("/admin/bids", response_class=HTMLResponse)
async def admin_bids(
    request: Request, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Adminlik huquqi yo'q")
    
    bids = db.query(models.Bid).order_by(models.Bid.created_at.desc()).all()
    return templates.TemplateResponse(
        "admin_bids.html", 
        {"request": request, "bids": bids, "user": current_user}
    )

@app.post("/admin/plate/{plate_id}/toggle")
async def toggle_plate_status(
    plate_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Adminlik huquqi yo'q")
    
    plate = db.query(models.AutoPlate).filter(models.AutoPlate.id == plate_id).first()
    if not plate:
        raise HTTPException(status_code=404, detail="Raqam topilmadi")
    
    plate.is_active = not plate.is_active
    db.commit()
    
    return RedirectResponse(
        url="/admin/plates",
        status_code=status.HTTP_302_FOUND
    )

@app.post("/admin/plate/new")
async def admin_create_plate(
    request: Request,
    plate_number: str = Form(...),
    description: str = Form(...),
    starting_price: float = Form(...),
    deadline: str = Form(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Check if plate number already exists
        existing_plate = db.query(models.AutoPlate).filter(
            models.AutoPlate.plate_number == plate_number
        ).first()
        
        if existing_plate:
            return templates.TemplateResponse(
                "admin_plate_form.html",
                {
                    "request": request,
                    "error": "Bu raqam allaqachon mavjud",
                    "user": current_user,
                    "now": datetime.now()
                },
                status_code=400
            )

        # Validate minimum price
        if starting_price < 1000:
            raise ValueError("Minimal summa 1000 so'mdan kam bo'lmasligi kerak")
            
        deadline_dt = datetime.fromisoformat(deadline)
        
        # Validate deadline
        if deadline_dt <= datetime.now():
            raise ValueError("Tugash muddati kelajakda bo'lishi kerak")

        plate = models.AutoPlate(
            plate_number=plate_number.upper(),  # Convert to uppercase
            description=description,
            starting_price=Decimal(str(starting_price)),
            deadline=deadline_dt,
            created_by_id=current_user.id,
            is_active=True
        )
        
        db.add(plate)
        db.commit()
        
        return RedirectResponse(
            url="/admin/plates",
            status_code=status.HTTP_302_FOUND
        )
        
    except ValueError as e:
        return templates.TemplateResponse(
            "admin_plate_form.html",
            {
                "request": request,
                "error": str(e),
                "user": current_user,
                "now": datetime.now()
            },
            status_code=400
        )
    except IntegrityError:
        return templates.TemplateResponse(
            "admin_plate_form.html",
            {
                "request": request,
                "error": "Bu raqam allaqachon mavjud",
                "user": current_user,
                "now": datetime.now()
            },
            status_code=400
        )
    except Exception as e:
        return templates.TemplateResponse(
            "admin_plate_form.html",
            {
                "request": request,
                "error": "Xatolik yuz berdi",
                "user": current_user,
                "now": datetime.now()
            },
            status_code=400
        )

@app.post("/admin/plate/{plate_id}/edit")
async def admin_update_plate(
    request: Request,
    plate_id: int,
    plate_number: str = Form(...),
    description: str = Form(...),
    starting_price: float = Form(...),
    deadline: str = Form(...),
    is_active: bool = Form(False),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        deadline_dt = datetime.fromisoformat(deadline)
        
        plate_update = schemas.AutoPlateUpdate(
            plate_number=plate_number,
            description=description,
            starting_price=Decimal(str(starting_price)),
            deadline=deadline_dt,
            is_active=is_active
        )
        
        update_plate(plate_id, plate_update, current_user, db)
        return RedirectResponse(
            url="/admin/plates",
            status_code=status.HTTP_302_FOUND
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "admin_plate_form.html",
            {
                "request": request,
                "error": str(e),
                "user": current_user,
                "plate": db.query(models.AutoPlate).filter(models.AutoPlate.id == plate_id).first(),
                "now": datetime.now()
            },
            status_code=400
        )

@app.post("/web/register")
async def web_register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Check if username already exists
        existing_user = get_user_by_username(db, username)
        if existing_user:
            return templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "error": "Bu username allaqachon mavjud"
                }
            )
        
        # Create new user
        hashed_password = get_password_hash(password)
        user = models.User(
            username=username,
            email=email,
            password=hashed_password,
            is_staff=False
        )
        db.add(user)
        db.commit()
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        # Redirect to home page with token
        response = RedirectResponse(
            url="/", 
            status_code=status.HTTP_302_FOUND
        )
        response.set_cookie(
            key="token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=1800
        )
        return response
        
    except Exception as e:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Ro'yxatdan o'tishda xatolik yuz berdi"
            }
        )

@app.post("/web/place-bid/{plate_id}")
async def web_place_bid(
    request: Request,
    plate_id: int,
    amount: float = Form(...),
    db: Session = Depends(get_db)
):
    # Get token from cookie
    token = request.cookies.get("token")
    if not token or not token.startswith("Bearer "):
        return RedirectResponse(
            url="/login-page?next=/plate/" + str(plate_id),
            status_code=status.HTTP_302_FOUND
        )
    
    try:
        # Extract actual token
        token = token.split("Bearer ")[1]
        # Verify token and get user
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401)
        
        user = get_user_by_username(db, username)
        if not user:
            raise HTTPException(status_code=401)
            
        # Create bid using schema
        bid = schemas.BidCreate(amount=amount, plate_id=plate_id)
        
        # Create bid using existing endpoint logic
        await create_bid(bid, user, db)
        
        return RedirectResponse(
            url=f"/plate/{plate_id}",
            status_code=status.HTTP_302_FOUND
        )
        
    except jwt.JWTError:
        return RedirectResponse(
            url="/login-page",
            status_code=status.HTTP_302_FOUND
        )
    except HTTPException as e:
        # Return to plate page with error
        plate = db.query(models.AutoPlate).filter(models.AutoPlate.id == plate_id).first()
        bids = db.query(models.Bid).filter(
            models.Bid.plate_id == plate_id
        ).order_by(models.Bid.amount.desc()).all()
        
        highest_bid = bids[0].amount if bids else 0
        
        return templates.TemplateResponse(
            "plate_detail.html",
            {
                "request": request,
                "plate": plate,
                "bids": bids,
                "highest_bid": highest_bid,
                "error": e.detail
            }
        )

@app.post("/web/login")
async def web_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
    db: Session = Depends(get_db)
):
    try:
        user = authenticate_user(db, username, password)
        if not user:
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": "Noto'g'ri login yoki parol"
                }
            )
        
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        response = RedirectResponse(
            url=next, 
            status_code=status.HTTP_302_FOUND
        )
        response.set_cookie(
            key="token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=1800  # 30 minutes
        )
        return response
        
    except Exception as e:
        print(f"Login error: {str(e)}")  # For debugging
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Tizimga kirishda xatolik yuz berdi"
            }
        )

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="token")
    return response

# Create an admin user if none exists
def create_admin_user():
    db = SessionLocal()
    try:
        admin = get_user_by_username(db, "admin")
        if not admin:
            hashed_password = get_password_hash("admin")
            admin_user = models.User(
                username="admin",
                email="admin@example.com",
                password=hashed_password,
                is_staff=True
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created!")
    finally:
        db.close()

if __name__ == "__main__":
    # Create necessary directories
    for dir_path in ["static/css", "static/js", "templates"]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Create admin user
    create_admin_user()
    
    # Run the app
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)