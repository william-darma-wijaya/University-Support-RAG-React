import streamlit as st
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from helpers.database import SessionLocal, engine
from model.models import Base, ChatSession
from helpers.langchain_handler import create_rag_chain, convert_to_chat_history

import uuid

# Make sure tables exist (same as in FastAPI)
Base.metadata.create_all(bind=engine)


# ---------- Utility DB helpers ----------

def get_db() -> Session:
    """Create a new SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_new_session(topic: str) -> ChatSession:
    """Create a new ChatSession row and return it."""
    db = SessionLocal()
    try:
        session_id = str(uuid.uuid4())
        new_session = ChatSession(
            session_id=session_id,
            topic=topic,
            messages=[]
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session
    finally:
        db.close()


def load_all_sessions():
    db = SessionLocal()
    try:
        return db.query(ChatSession).all()
    finally:
        db.close()


def load_session_by_id(session_id: str):
    db = SessionLocal()
    try:
        return db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    finally:
        db.close()


def chat_with_session(session_id: str, user_input: str) -> str:
    """Run one chat turn against the RAG chain, update DB, return assistant response."""
    db = SessionLocal()
    try:
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            raise ValueError("Session not found in DB")

        # Rebuild chat history for RAG
        history = convert_to_chat_history(session.messages or [])

        # Create chain with current DB session
        rag_chain = create_rag_chain(db_session=db)

        # Call your existing RAG chain API
        response = rag_chain.ask(
            question=user_input,
            chat_history=history,
            session_id=session_id
        )

        # Persist messages
        session.messages.append({"role": "user", "message": user_input})
        session.messages.append({"role": "assistant", "message": response})

        flag_modified(session, "messages")
        db.commit()

        return response
    finally:
        db.close()


# ---------- Streamlit UI ----------

st.set_page_config(page_title="RAG Chat Sessions", page_icon="💬", layout="wide")

st.title("💬 RAG Chat Sessions (Streamlit)")

# Keep current session ID and messages in Streamlit state
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "current_topic" not in st.session_state:
    st.session_state.current_topic = None
if "current_messages" not in st.session_state:
    st.session_state.current_messages = []


# ----- Sidebar: Session management -----
st.sidebar.header("Session Management")

# Create new session
with st.sidebar.expander("➕ Create New Session", expanded=True):
    new_topic = st.text_input("Topic", key="new_topic_input")
    if st.button("Create session"):
        if not new_topic.strip():
            st.warning("Please enter a topic.")
        else:
            new_session = create_new_session(new_topic.strip())
            st.session_state.current_session_id = new_session.session_id
            st.session_state.current_topic = new_session.topic
            st.session_state.current_messages = new_session.messages or []
            st.success(f"Created session: {new_session.session_id}")

# List & select existing sessions
st.sidebar.markdown("---")
st.sidebar.subheader("Existing Sessions")

sessions = load_all_sessions()
if not sessions:
    st.sidebar.info("No sessions yet.")
else:
    options = {
        f"{s.topic or '(no topic)'} — {s.session_id}": s.session_id
        for s in sessions
    }

    selected_label = st.sidebar.selectbox(
        "Select a session",
        ["(none)"] + list(options.keys()),
        index=0
    )

    if selected_label != "(none)":
        selected_id = options[selected_label]
        if st.sidebar.button("Load session"):
            sel = load_session_by_id(selected_id)
            if sel:
                st.session_state.current_session_id = sel.session_id
                st.session_state.current_topic = sel.topic
                st.session_state.current_messages = sel.messages or []
                st.sidebar.success("Session loaded.")


# ----- Main Area: Chat -----

if not st.session_state.current_session_id:
    st.info("Create or select a session from the sidebar to start chatting.")
else:
    st.markdown(f"### Current session: `{st.session_state.current_session_id}`")
    st.markdown(f"**Topic:** {st.session_state.current_topic or '-'}")

    # Show history
    st.markdown("#### History")
    if not st.session_state.current_messages:
        st.write("_No messages yet. Start the conversation below._")
    else:
        # If you have Streamlit chat components, use them:
        try:
            for msg in st.session_state.current_messages:
                role = msg.get("role", "user")
                text = msg.get("message", "")
                with st.chat_message("assistant" if role == "assistant" else "user"):
                    st.markdown(text)
        except Exception:
            # Fallback rendering if st.chat_message is not available
            for msg in st.session_state.current_messages:
                role = msg.get("role", "user")
                text = msg.get("message", "")
                if role == "user":
                    st.markdown(f"**You:** {text}")
                else:
                    st.markdown(f"**Assistant:** {text}")

    st.markdown("---")
    # Chat input
    user_input = st.chat_input("Type your message...")

    if user_input:
        with st.spinner("Thinking..."):
            try:
                response = chat_with_session(
                    session_id=st.session_state.current_session_id,
                    user_input=user_input
                )
                # Update local state so UI refreshes immediately
                st.session_state.current_messages.append({"role": "user", "message": user_input})
                st.session_state.current_messages.append({"role": "assistant", "message": response})

                # Re-render messages (Streamlit does this on rerun)
            except Exception as e:
                st.error(f"Error while chatting: {e}")
