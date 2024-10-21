from fastapi import FastAPI,Body,Form
from starlette.responses import HTMLResponse,FileResponse,RedirectResponse
app = FastAPI()

# @app.get("/")
# async def root():
#     return {"message": "Salom! Bu mening FastAPI ilovam"}

@app.get("/")
def root():
    return FileResponse("public/index.html")
@app.post("postdata")
def postdata(username=Form(),userage=Form()):
    return {"name":username,"age":userage}



@app.get("/about-us")
def main_func():
    return HTMLResponse(content="<p>Salom PDP<p>")

@app.get("/file",response_class=FileResponse)
def file():
    return "public/index.html"

@app.get("/users/{name}/{age}")
def users(name,age):
    return f"Saom {name} va {age}"
"""
GET: Resursni olish uchun ishlatiladi.
POST: Yangi resurs yaratish uchun ishlatiladi.
PUT: Mavjud resursni yangilash uchun ishlatiladi.
PATCH: Mavjud resursning bir qismini yangilash uchun ishlatiladi.
DELETE: Resursni o'chirish uchun ishlatiladi.
OPTIONS: Resurs uchun mavjud bo'lgan HTTP metodlarini olish uchun ishlatiladi.
HEAD: GET so'roviga o'xshash, lekin faqat javob sarlavhalarini qaytaradi, javob tanasini emas.
TRACE: So'rovni diagnostika qilish uchun ishlatiladi.
"""

users = {
    "John Doe": 1,
    "Jane Doe": 2,
    "Peter Jones": 3,
    "Alice Smith": 4,
    "Bob Johnson": 5,
    "Sarah Williams": 6,
    "David Brown": 7,
    "Emily Miller": 8,
    "Michael Davis": 9,
    "Jessica Garcia": 10,
}

@app.get("/get_id/{name}")
async def get_id(name: str):
    """
    Foydalanuvchi ismini qabul qilib, uning ID sini qaytaradi.
    """
    if name in users:
        return {"id": users[name]} and RedirectResponse("old")
    else:
        return {"message": "Foydalanuvchi topilmadi"}

@app.get("/all")
async def get_all(name: str, age: int):
    """
    Ism va yoshni qabul qilib, ularni lug'atda qaytaradi.
    """
    return {"name": name, "age": age}

@app.get("/old")
def redirect():
    return RedirectResponse("new")
@app.get("/new")
def new():
    return "Yangigi versiya"

@app.post("/add")
def func_n(name=Body(min_length=3,max_length=15),age=Body(gt=3,lt=30)):

    return f"salom{name}  {age}"
