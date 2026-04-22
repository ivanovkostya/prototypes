from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

engine = create_engine("sqlite:///students.db")

SessionLocal = sessionmaker(bind=engine)

# создаём таблицы
Base.metadata.create_all(bind=engine)