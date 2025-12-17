from sqlalchemy import Column, String, JSON, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, declarative_base, relationship

from helpers.database import Base

Base = declarative_base()

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(String, primary_key=True, index=True)
    topic = Column(String)
    messages = Column(JSON)

    # new: owner of the session (user id)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # optional convenient relationship
    owner = relationship("User", back_populates="sessions")

# keep other models (User, ProcessedFile) unchanged, but add backref on User:
class ProcessedFile(Base):
    __tablename__ = "processed_files"
    
    filename = Column(String(255), primary_key=True, index=True, nullable=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # optionally add sessions relationship
    sessions = relationship("ChatSession", back_populates="owner", cascade="all, delete-orphan")