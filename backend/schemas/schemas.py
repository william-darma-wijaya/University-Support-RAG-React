from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    user_input: str

class Message(BaseModel):
    role: str
    message: str

class SessionHistory(BaseModel):
    session_id: str
    topic: Optional[str]
    messages: List[Message]

class SessionSummary(BaseModel):
    session_id: str
    topic: Optional[str]

class CreateSessionRequest(BaseModel):
    topic: str

class CreateSessionResponse(BaseModel):
    message: str
    session_id: str
    topic: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
