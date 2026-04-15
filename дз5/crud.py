from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Student
import csv
import os

# ---------------- CRUD ----------------

def create_student(db: Session, data: dict):
    student = Student(**data)
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def get_all_students(db: Session):
    return db.query(Student).all()


def update_student(db: Session, student_id: int, data: dict):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return None

    for key, value in data.items():
        setattr(student, key, value)

    db.commit()
    return student


def delete_student(db: Session, student_id: int):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return None

    db.delete(student)
    db.commit()
    return student


# ---------------- CSV ----------------

def load_from_csv(db: Session, file_path=None):
    import os, csv
    from models import Student

    if file_path is None:
        file_path = os.path.join(os.path.dirname(__file__), "students.csv")

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


# ---------------- ЗАПРОСЫ ----------------

# по факультету
def get_students_by_faculty(db: Session, faculty: str):
    return db.query(Student).filter(Student.faculty == faculty).all()


# уникальные курсы
def get_unique_courses(db: Session):
    return db.query(Student.course).distinct().all()


# студенты с оценкой < 30
def get_failed_students(db: Session, course: str):
    return db.query(Student).filter(
        Student.course == course,
        Student.grade < 30
    ).all()


# средний балл по факультету
def get_avg_grade(db: Session, faculty: str):
    return db.query(func.avg(Student.grade)).filter(
        Student.faculty == faculty
    ).scalar()