from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import hashlib

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Ma'lumotlar bazasiga ulanish funksiyasi
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Foydalanuvchi qo'shish funksiyasi
def add_user(conn, username, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        print(f"Foydalanuvchi '{username}' qo'shildi.")
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail=f"Xato: Foydalanuvchi '{username}' allaqachon mavjud.")

# Foydalanuvchini tekshirish funksiyasi
def check_user(conn, username, password):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    if user:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if hashed_password == user['password']:
            print("Login muvaffaqiyatli!")
            return True
        else:
            print("Noto'g'ri parol.")
            return False
    else:
        print("Foydalanuvchi topilmadi.")
        return False

# Jadval yaratish
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
''')
conn.commit()
conn.close()

# Ro'yxatdan o'tish sahifasi
@app.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# Ro'yxatdan o'tishni qayta ishlash
@app.post("/register", response_class=RedirectResponse)
async def register_post(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    add_user(conn, username, password)
    conn.close()
    return RedirectResponse(url="/", status_code=303)

# Login sahifasi
@app.get("/", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Loginni qayta ishlash
@app.post("/", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    if check_user(conn, username, password):
        return templates.TemplateResponse("next_page.html", {"request": request, "username": username})
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Noto'g'ri login yoki parol"})
    conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)