from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from helpers.database import SessionLocal, engine, get_db
from model.models import Base, ChatSession
from schemas.schemas import (
    ChatRequest, SessionHistory,
    SessionSummary, CreateSessionRequest, CreateSessionResponse,
    Token, TokenData
)
from typing import List
from helpers.langchain_handler import create_rag_chain, convert_to_chat_history
import uuid
import os
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from model.models import User

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        print("DEBUG: incoming token (truncated):", token[:64] if token else None)
    except Exception:
        print("DEBUG: incoming token: <unprintable>")
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        print("DEBUG: JWT decode error:", repr(e))
        raise credentials_exception

    user = get_user_by_username(db, token_data.username)
    if user is None:
        raise credentials_exception
    return user

Base.metadata.create_all(bind=engine)

app = FastAPI()
# uvicorn fast_api:app --reload
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/session", response_model=CreateSessionResponse)
def create_session(req: CreateSessionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session_id = str(uuid.uuid4())

    new_session = ChatSession(
        session_id=session_id,
        topic=req.topic,
        messages=[],
        owner_id=current_user.id
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return CreateSessionResponse(
        message="Session created successfully.",
        session_id=session_id,
        topic=req.topic
    )

@app.post("/chat/{session_id}")
def chat(session_id: str, req: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not permitted to access this session.")

    history = convert_to_chat_history(session.messages or [])
    rag_chain = create_rag_chain(db_session=db)

    response = rag_chain.ask(
        question=req.user_input,
        chat_history=history,
        session_id=session_id
    )

    session.messages.append({"role": "user", "message": req.user_input})
    session.messages.append({"role": "assistant", "message": response})
    flag_modified(session, "messages")
    db.commit()
    db.refresh(session)
    return {
    "session_id": str(session.session_id),
    "topic": session.topic,
    "messages": session.messages
}


@app.get("/history/{session_id}", response_model=SessionHistory)
def get_history(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not permitted to access this session.")
    return {
        "session_id": str(session.session_id),
        "topic": session.topic,
        "messages": session.messages or []
    }

@app.get("/sessions", response_model=List[SessionSummary])
def get_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(ChatSession).filter(ChatSession.owner_id == current_user.id).all()
    return [
        {"session_id": str(s.session_id), "topic": s.topic} for s in sessions
    ]

@app.post("/chat/{session_id}/edit_last")
def edit_last_message(session_id: str, req: ChatRequest = Body(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not permitted to edit this session.")

    msgs = session.messages or []

    last_user_idx = None
    for i in range(len(msgs) - 1, -1, -1):
        if msgs[i].get("role") == "user":
            last_user_idx = i
            break
    if last_user_idx is None:
        raise HTTPException(status_code=400, detail="No user message found to edit.")
    msgs[last_user_idx]["message"] = req.user_input
    trimmed = msgs[: last_user_idx + 1]
    history = convert_to_chat_history(trimmed)
    rag_chain = create_rag_chain(db_session=db)
    new_response = rag_chain.ask(
        question=req.user_input,
        chat_history=history,
        session_id=session_id
    )
    trimmed.append({"role": "assistant", "message": new_response})
    session.messages = trimmed
    flag_modified(session, "messages")
    db.commit()
    db.refresh(session)
    return {"messages": session.messages}

@app.delete("/session/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not permitted to delete this session.")
    db.delete(session)
    db.commit()
    return {"message": "Session deleted successfully"}

@app.post("/register")
def register(user_in: dict, db: Session = Depends(get_db)):
    """
    POST /register
    Request body: {"username": "...", "password": "..."}
    """
    username = user_in.get("username")
    password = user_in.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")


    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed = get_password_hash(password)
    user = User(username=username, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created", "username": user.username}

@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}
