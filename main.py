import uuid
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlmodel import Session, select
from fastapi.staticfiles import StaticFiles
import os


from database import init_db, engine, get_session
from models import Contact, User

from webchat import qa, is_fee_question, is_course_question

print("PORT:", os.getenv("PORT")) 

app = FastAPI(title="Zen Chatbot Backend (Local)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Serve frontend if you put it in backend/static (optional)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.on_event("startup")
def on_startup():
    init_db()

class ChatRequest(BaseModel):
    user_id: str | None = None
    question: str

class ContactRequest(BaseModel):
    user_id: str | None = None
    name: str
    phone: str
    email: str
    course: str
    triggered_question: str | None = None

@app.get("/")
def home():
    return RedirectResponse(url="/static/index.html")

@app.get("/create_user")
def create_user():
    user_id = str(uuid.uuid4())
    u = User(id=user_id)
    with Session(engine) as s:
        s.add(u)
        s.commit()
    return {"user_id": user_id}

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    # check user_id presence; allow guest but prefer user_id
    user_id = req.user_id
    question = req.question or ""

    # decide show_form if fee/course related
    show_form = False
    if is_fee_question(question) or (is_course_question(question) and any(k in question.lower() for k in ["fee", "cost", "price"])):
        show_form = True

    # When not fee-related, call the qa module
    answer = qa(question) if not show_form else "Please fill the form for complete fee/course enrollment details."

    return {"answer": answer, "show_form": show_form, "user_id": user_id}

@app.post("/save_contact")
def save_contact(payload: ContactRequest):
    # Save to DB
    contact = Contact(
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        course=payload.course,
        triggered_question=payload.triggered_question
    )
    with Session(engine) as s:
        s.add(contact)
        s.commit()
        s.refresh(contact)
    return {"message": "Saved", "id": contact.id}

@app.get("/inquiries")
def list_inquiries():
    with Session(engine) as s:
        contacts = s.exec(select(Contact)).all()
        # convert to dicts
        data = []
        for c in contacts:
            data.append({
                "id": c.id,
                "name": c.name,
                "phone": c.phone,
                "email": c.email,
                "course": c.course,
                "triggered_question": c.triggered_question,
                "created_at": c.created_at
            })
    return {"inquiries": data}
