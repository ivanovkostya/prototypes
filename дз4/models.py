from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    last_name = Column(String)
    first_name = Column(String)
    faculty = Column(String)
    course = Column(String)
    grade = Column(Integer)
