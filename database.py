from sqlmodel import create_engine, Session
from models import Contact, User, SQLModel
import os

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./inquiries.db")
engine = create_engine(DB_URL, echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
