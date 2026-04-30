import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Student, User

# Создаём тестовое приложение без Redis
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
import crud

app = FastAPI()

# Тестовая БД
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def get_db():
    db = TestingSessionLocal()
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

# Эндпоинты
@app.get("/students")
def get_students(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return crud.get_all_students(db)

@app.post("/students")
def create_student(student: dict, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return crud.create_student(db, student)

@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return crud.delete_student(db, student_id)

@app.get("/faculty/{faculty}")
def by_faculty(faculty: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return crud.get_students_by_faculty(db, faculty)

@app.get("/failed/{course}")
def failed(course: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return crud.get_failed_students(db, course)

client = TestClient(app)

# Вспомогательные функции
def create_test_user():
    db = TestingSessionLocal()
    # Очищаем перед созданием
    db.query(User).delete()
    user = User(username="testuser", password="123456")
    db.add(user)
    db.commit()
    db.close()

def clear_db():
    db = TestingSessionLocal()
    db.query(Student).delete()
    db.query(User).delete()
    db.commit()
    db.close()


# ==================== ТЕСТЫ ====================

def test_create_student_success():
    clear_db()
    create_test_user()
    
    response = client.post(
        "/students",
        json={
            "last_name": "Иванов",
            "first_name": "Иван",
            "faculty": "АВТФ",
            "course": "Программирование",
            "grade": 85
        },
        auth=("testuser", "123456")
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["last_name"] == "Иванов"
    assert data["grade"] == 85


def test_create_student_no_auth():
    clear_db()
    
    response = client.post(
        "/students",
        json={
            "last_name": "Петров",
            "first_name": "Петр",
            "faculty": "ФПМИ",
            "course": "Алгебра",
            "grade": 90
        }
    )
    
    assert response.status_code == 401


def test_get_students_success():
    clear_db()
    create_test_user()
    
    # Создаём студента
    client.post(
        "/students",
        json={"last_name": "Сидоров", "first_name": "Сидор", 
              "faculty": "ФЛА", "course": "Физика", "grade": 78},
        auth=("testuser", "123456")
    )
    
    response = client.get("/students", auth=("testuser", "123456"))
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["last_name"] == "Сидоров"


def test_get_students_empty():
    clear_db()
    create_test_user()
    
    response = client.get("/students", auth=("testuser", "123456"))
    
    assert response.status_code == 200
    assert response.json() == []


def test_delete_student_success():
    clear_db()
    create_test_user()
    
    # Создаём студента
    resp = client.post(
        "/students",
        json={"last_name": "Ким", "first_name": "Петр", 
              "faculty": "ФПМИ", "course": "МатАн", "grade": 28},
        auth=("testuser", "123456")
    )
    student_id = resp.json()["id"]
    
    # Удаляем
    response = client.delete(f"/students/{student_id}", auth=("testuser", "123456"))
    
    assert response.status_code == 200
    # Проверяем, что список пуст
    get_resp = client.get("/students", auth=("testuser", "123456"))
    assert len(get_resp.json()) == 0


def test_delete_student_not_found():
    clear_db()
    create_test_user()
    
    response = client.delete("/students/99999", auth=("testuser", "123456"))
    
    assert response.status_code == 200
    assert response.json() is None


def test_get_by_faculty_success():
    clear_db()
    create_test_user()
    
    # Создаём двух студентов на одном факультете
    client.post(
        "/students",
        json={"last_name": "Иванов", "first_name": "Иван", 
              "faculty": "АВТФ", "course": "Теория", "grade": 90},
        auth=("testuser", "123456")
    )
    client.post(
        "/students",
        json={"last_name": "Петров", "first_name": "Петр", 
              "faculty": "АВТФ", "course": "Теория", "grade": 85},
        auth=("testuser", "123456")
    )
    
    response = client.get("/faculty/АВТФ", auth=("testuser", "123456"))
    
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_by_faculty_empty():
    clear_db()
    create_test_user()
    
    response = client.get("/faculty/НЕТ_ТАКОГО", auth=("testuser", "123456"))
    
    assert response.status_code == 200
    assert response.json() == []


def test_get_failed_students_success():
    clear_db()
    create_test_user()
    
    # Студент с двойкой (оценка < 30)
    client.post(
        "/students",
        json={"last_name": "Райт", "first_name": "Вероника", 
              "faculty": "ФЛА", "course": "Теор. Механика", "grade": 7},
        auth=("testuser", "123456")
    )
    # Студент с хорошей оценкой
    client.post(
        "/students",
        json={"last_name": "Ли", "first_name": "Иван", 
              "faculty": "АВТФ", "course": "Теор. Механика", "grade": 85},
        auth=("testuser", "123456")
    )
    
    response = client.get("/failed/Теор. Механика", auth=("testuser", "123456"))
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["last_name"] == "Райт"


def test_get_failed_students_no_fails():
    clear_db()
    create_test_user()
    
    client.post(
        "/students",
        json={"last_name": "Ли", "first_name": "Иван", 
              "faculty": "АВТФ", "course": "Физика", "grade": 85},
        auth=("testuser", "123456")
    )
    
    response = client.get("/failed/Физика", auth=("testuser", "123456"))
    
    assert response.status_code == 200
    assert response.json() == []