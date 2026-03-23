from sqlalchemy import create_engine
from models import Base

engine = create_engine("sqlite:///students.db")

if __name__ == "__main__":
    Base.metadata.create_all(engine)
