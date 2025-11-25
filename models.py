from sqlmodel import SQLModel, Field
from typing import Optional
import time

class Contact(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    phone: str
    email: str
    course: str
    triggered_question: Optional[str] = None
    created_at: float = Field(default_factory=time.time)

class User(SQLModel, table=True):
    id: str = Field(primary_key=True)
    contact_saved: Optional[bool] = False
    created_at: float = Field(default_factory=time.time)
