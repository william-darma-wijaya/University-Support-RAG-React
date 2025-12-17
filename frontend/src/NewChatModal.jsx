import React, { useState, useEffect, useRef } from "react";
import "./ConfirmModal.css";

export default function NewChatModal({ open, onCancel, onCreate }) {
  const [topic, setTopic] = useState("");
  const inputRef = useRef(null);

  useEffect(() => {
    if (open) {
      setTopic("");
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  if (!open) return null;

  const handleOk = () => {
    const t = (topic || "").trim();
    if (!t) return; 
    onCreate(t);
  };

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal-panel" role="document">
        <header className="modal-header">
          <h3>Create New Chat</h3>
        </header>

        <div className="modal-body">
          <label style={{ fontWeight: 600 }}>Chat Topic:</label>
          <input
            ref={inputRef}
            type="text"
            className="modal-input"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Enter topic..."
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                handleOk();
              } else if (e.key === "Escape") {
                onCancel();
              }
            }}
          />
        </div>

        <footer className="modal-footer">
          <button className="btn btn-secondary" onClick={onCancel}>Cancel</button>
          <button
            className="btn btn-primary"
            onClick={handleOk}
            style={{ marginLeft: 12 }}
          >
            OK
          </button>
        </footer>
      </div>
    </div>
  );
}
