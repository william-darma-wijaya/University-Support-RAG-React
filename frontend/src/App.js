import React, { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  useNavigate,
  Navigate,
  useLocation,
} from "react-router-dom";
import { api } from "./api";

import Login from "./Login";
import Register from "./Register";
import ConfirmModal from "./ConfirmModal";
import ChatInterface from "./ChatInterface";
import NewChatModal from "./NewChatModal";


import { MessageSquare } from "lucide-react";
import "./App.css";

import { Trash2 } from "lucide-react";

const Sidebar = ({ sessions, onCreateSession, onSelectSession, onDeleteRequest, activeId }) => {
  return (
    <div className="sidebar">

      <button className="sidebar-button" onClick={onCreateSession}>
        + New Chat
      </button>
      <div className="sidebar-divider"></div>
      <div className="sidebar-sessions">
        {sessions.map((s) => (
          <div
            key={s.session_id}
            className={"sidebar-session-item " + (s.session_id === activeId ? "active" : "")}
            onClick={() => onSelectSession(s.session_id)}
          >
            <span>{s.topic || "Untitled Session"}</span>

            <Trash2
              size={16}
              className="sidebar-delete"
              onClick={(e) => {
                e.stopPropagation();
                if (typeof onDeleteRequest === "function") {
                  onDeleteRequest(s.session_id, s.topic);
                }
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

const RequireAuth = ({ auth, children }) => {
  if (!auth) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

const ProtectedLayout = ({ sessions, onCreateSession, onSelectSession, onDeleteRequest, children, onLogout, activeId }) => {
  return (
    <div className="main-layout">
      <Sidebar
        sessions={sessions}
        onCreateSession={onCreateSession}
        onSelectSession={onSelectSession}
        onDeleteRequest={onDeleteRequest}
        activeId={activeId}  
      />

      <div className="content-area">
        <header className="app-header">
          <div className="header-left" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <MessageSquare size={24} color="#0497db" />
            <span className="header-title">BINUS Support Chat Bot</span>
          </div>
          <div className="header-right">
            <button className="logout-button" onClick={onLogout}>Logout</button>
          </div>
        </header>

        <main className="content-main">{children}</main>
      </div>
    </div>
  );
};

function AppInner() {
  const [sessions, setSessions] = useState([]);
  const [auth, setAuth] = useState(!!localStorage.getItem("access_token"));
  const navigate = useNavigate();
  const location = useLocation();

  const activeMatch = location.pathname.match(/^\/chat\/([^/]+)/);
  const activeId = activeMatch ? activeMatch[1] : null;


  const [confirmOpen, setConfirmOpen] = useState(false);
  const [toDeleteSessionId, setToDeleteSessionId] = useState(null);
  const [toDeleteSessionTopic, setToDeleteSessionTopic] = useState("");
  const [newChatOpen, setNewChatOpen] = useState(false);

  
  useEffect(() => {
    if (auth) {
      api
        .getSessions()
        .then(setSessions)
        .catch((err) => {
          console.error(err);
          if (err.response?.status === 401) {
            api.logout();
            setAuth(false);
            navigate("/login");
          }
        });
    } else {
      setSessions([]);
    }
  }, [auth, navigate]);

const handleCreate = () => {
  setNewChatOpen(true);
};

const handleCreateNewChat = async (topic) => {
  setNewChatOpen(false);

  const newSession = await api.createSession(topic);
  setSessions((prev) => [...prev, newSession]);
  navigate(`/chat/${newSession.session_id}`);
};

  const handleDeleteSession = async (sessionId) => {
    try {
      await api.deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
      if (window.location.pathname.includes(sessionId)) navigate("/");
    } catch (err) {
      console.error(err);
      alert("Failed to delete session.");
    }
  };

  const handleLogout = () => {
    api.logout();
    setAuth(false);
    navigate("/login");
  };

  const handleAuthFailed = () => {
    api.logout();
    setAuth(false);
    navigate("/login");
  };

  const handleDeleteRequest = (sessionId, topic) => {
    setToDeleteSessionId(sessionId);
    setToDeleteSessionTopic(topic || "");
    setConfirmOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!toDeleteSessionId) {
      setConfirmOpen(false);
      return;
    }
    try {
      await api.deleteSession(toDeleteSessionId);
      setSessions((prev) => prev.filter((s) => s.session_id !== toDeleteSessionId));
      if (window.location.pathname.includes(toDeleteSessionId)) navigate("/");
    } catch (err) {
      console.error(err);
      alert("Failed to delete session.");
    } finally {
      setConfirmOpen(false);
      setToDeleteSessionId(null);
      setToDeleteSessionTopic("");
    }
  };

  const handleCancelDelete = () => {
    setConfirmOpen(false);
    setToDeleteSessionId(null);
    setToDeleteSessionTopic("");
  };

  return (
    <>
      <Routes>
        <Route path="/login" element={<Login onLogin={() => setAuth(true)} />} />
        <Route path="/register" element={<Register onRegister={() => setAuth(true)} />} />

        <Route
          path="/*"
          element={
            <RequireAuth auth={auth}>
              <ProtectedLayout
                sessions={sessions}
                onCreateSession={handleCreate}
                onSelectSession={(id) => navigate(`/chat/${id}`)}
                onDeleteRequest={handleDeleteRequest}
                onLogout={handleLogout}
                activeId={activeId}
              >
                <Routes>
                  <Route path="/" element={<div style={{ padding: "2rem" }}>Select or create a chat to begin</div>} />
                  <Route path="chat/:id" element={<ChatInterface onAuthFailed={handleAuthFailed} />} />
                </Routes>
              </ProtectedLayout>
            </RequireAuth>
          }
        />
      </Routes>

      <ConfirmModal
        open={confirmOpen}
        title="Delete this session?"
        message={`Delete this session${toDeleteSessionTopic ? ` (“${toDeleteSessionTopic}”)` : ""}? This cannot be undone.`}
        onCancel={handleCancelDelete}
        onConfirm={handleConfirmDelete}
      />
      <NewChatModal
        open={newChatOpen}
        onCancel={() => setNewChatOpen(false)}
        onCreate={handleCreateNewChat}
      />
    </>
  );
}


export default function App() {
  return (
    <Router>
      <AppInner />
    </Router>
  );
}
