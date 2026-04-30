from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from db import SessionLocal, engine
from models import Base, User
import crud
import uvicorn
import redis
import json
from functools import wraps


app = FastAPI()

# создаём таблицы
Base.metadata.create_all(bind=engine)

# подключение к Redis
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

security = HTTPBasic()

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or user.password != password:
        return None
    return user

def get_current_user(credentials: HTTPBasicCredentials = Depends(security), 
                     db: Session = Depends(get_db)):
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверные учетные данные")
    return user


# декоратор для кэширования
def cache(ttl=60):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(kwargs)}:{str(args[1:])}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result, default=str))
            return result
        return wrapper
    return decorator


# ---------------- фоновые задачи ----------------

def background_load_csv(db_path: str, file_path: str):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from models import Student
    import csv
    engine = create_engine(db_path)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        with open(file_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                student = Student(
                    last_name=row["Фамилия"],
                    first_name=row["Имя"],
                    faculty=row["Факультет"],
                    course=row["Курс"],
                    grade=int(row["Оценка"])
                )
                db.add(student)
            db.commit()
    finally:
        db.close()

def background_delete_students(db_path: str, student_ids: list):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from models import Student
    engine = create_engine(db_path)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        for student_id in student_ids:
            student = db.query(Student).filter(Student.id == student_id).first()
            if student:
                db.delete(student)
        db.commit()
    finally:
        db.close()


@app.get("/auth/register")
def register(username: str, password: str, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    user = User(username=username, password=password)
    db.add(user)
    db.commit()
    return {"message": "OK"}

@app.get("/auth/login")
def login(credentials: HTTPBasicCredentials = Depends(HTTPBasic()), 
          db: Session = Depends(get_db)):
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Ошибка")
    return {"message": "OK"}

@app.get("/auth/logout")
def logout():
    return {"message": "OK"}


# ---------------- CRUD ----------------

@app.get("/students")
@cache(ttl=30)
async def get_students(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return crud.get_all_students(db)


@app.post("/students")
def create_student(student: dict, db: Session = Depends(get_db), _=Depends(get_current_user)):
    redis_client.delete("get_students:{}:()")
    return crud.create_student(db, student)


@app.put("/students/{student_id}")
def update_student(student_id: int, data: dict, db: Session = Depends(get_db), _=Depends(get_current_user)):
    redis_client.delete("get_students:{}:()")
    return crud.update_student(db, student_id, data)


@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    redis_client.delete("get_students:{}:()")
    return crud.delete_student(db, student_id)


# ---------------- фоновые задачи (эндпоинты) ----------------

@app.post("/load-csv")
def load_csv_background(file_path: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db), _=Depends(get_current_user)):
    db_path = "sqlite:///students.db"  #直接用 строку вместо engine.url
    background_tasks.add_task(background_load_csv, db_path, file_path)
    return {"status": "started", "message": f"Загрузка из {file_path} запущена в фоне"}

@app.post("/delete-students")
def delete_students_background(student_ids: list, background_tasks: BackgroundTasks, db: Session = Depends(get_db), _=Depends(get_current_user)):
    db_path = "sqlite:///students.db"  #直接用 строку
    background_tasks.add_task(background_delete_students, db_path, student_ids)
    redis_client.delete("get_students:{}:()")
    return {"status": "started", "message": f"Удаление {len(student_ids)} студентов запущено в фоне"}


# ---------------- ЗАПРОСЫ ----------------

@app.get("/faculty/{faculty}")
@cache(ttl=60)
async def by_faculty(faculty: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return crud.get_students_by_faculty(db, faculty)


@app.get("/courses")
@cache(ttl=120)
async def courses(db: Session = Depends(get_db)):
    return crud.get_unique_courses(db)


@app.get("/failed/{course}")
@cache(ttl=60)
async def failed(course: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return crud.get_failed_students(db, course)


@app.get("/avg/{faculty}")
@cache(ttl=60)
async def avg(faculty: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return crud.get_avg_grade(db, faculty)


# ---------------- CSV ----------------

@app.post("/load")
def load(db: Session = Depends(get_db), _=Depends(get_current_user)):
    crud.load_from_csv(db)
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)