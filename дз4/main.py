from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from db import SessionLocal, engine
from models import Base
import crud
import uvicorn


app = FastAPI()

# создаём таблицы
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- CRUD ----------------

@app.get("/students")
def get_students(db: Session = Depends(get_db)):
    return crud.get_all_students(db)


@app.post("/students")
def create_student(student: dict, db: Session = Depends(get_db)):
    return crud.create_student(db, student)


@app.put("/students/{student_id}")
def update_student(student_id: int, data: dict, db: Session = Depends(get_db)):
    return crud.update_student(db, student_id, data)


@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    return crud.delete_student(db, student_id)


# ---------------- ЗАПРОСЫ ----------------

@app.get("/faculty/{faculty}")
def by_faculty(faculty: str, db: Session = Depends(get_db)):
    return crud.get_students_by_faculty(db, faculty)


@app.get("/courses")
def courses(db: Session = Depends(get_db)):
    return crud.get_unique_courses(db)


@app.get("/failed/{course}")
def failed(course: str, db: Session = Depends(get_db)):
    return crud.get_failed_students(db, course)


@app.get("/avg/{faculty}")
def avg(faculty: str, db: Session = Depends(get_db)):
    return crud.get_avg_grade(db, faculty)


# ---------------- CSV ----------------

@app.post("/load")
def load(db: Session = Depends(get_db)):
    crud.load_from_csv(db)
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)