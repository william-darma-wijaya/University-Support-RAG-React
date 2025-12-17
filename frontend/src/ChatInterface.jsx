import React, { useState, useEffect, useRef } from "react";
import { useParams } from "react-router-dom";
import { Send } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { api } from "./api";
import "./ChatInterface.css";

export default function ChatInterface({ onAuthFailed }) {
  const { id } = useParams();

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [editingIndex, setEditingIndex] = useState(null);
  const [backupMessages, setBackupMessages] = useState([]);

  const messagesRef = useRef(null);

  useEffect(() => {
    if (!id) return;

    api.getHistory(id)
      .then((res) => setMessages(res.data.messages || []))
      .catch((err) => {
        if (err?.response?.status === 401 && onAuthFailed) {
          onAuthFailed();
        }
      });
  }, [id, onAuthFailed]);

  useEffect(() => {
    messagesRef.current?.scrollTo({
      top: messagesRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const lastUserIndex = [...messages]
    .map((m) => m.role)
    .lastIndexOf("user");

  const startEdit = () => {
    if (lastUserIndex === -1) return;

    setBackupMessages(messages);
    setInput(messages[lastUserIndex].message);
    setEditingIndex(lastUserIndex);

    setMessages(messages.slice(0, lastUserIndex + 1));
  };

  const cancelEdit = () => {
    setMessages(backupMessages);
    setBackupMessages([]);
    setEditingIndex(null);
    setInput("");
  };

const handleSend = async (e) => {
  e.preventDefault();
  if (!input.trim() || loading) return;

  const userText = input.trim();
  setInput("");
  setLoading(true);

  let nextMessages = [...messages];

  if (editingIndex !== null) {
    nextMessages[editingIndex] = { role: "user", message: userText };
    nextMessages = nextMessages.slice(0, editingIndex + 1);
  } else {
    nextMessages.push({ role: "user", message: userText });
  }

  nextMessages.push({
    role: "assistant",
    message: "Thinking…",
    _thinking: true,
  });

  setMessages(nextMessages);

  try {
    let res;

    if (editingIndex !== null) {
      res = await api.editLastMessage(id, userText);
      setEditingIndex(null);
    } else {
      res = await api.sendMessage(id, userText);
    }

    setMessages(res.data.messages || []);
  } catch (err) {
    console.error(err);
    setMessages((prev) =>
      prev.map((m) =>
        m._thinking
          ? { role: "assistant", message: "Error: failed to send message." }
          : m
      )
    );
  } finally {
    setLoading(false);
  }
};


  return (
    <div className="chat-interface">
      <div className="chat-messages" ref={messagesRef}>
        {messages.map((m, i) => {
          const isUser = m.role === "user";
          const isLastUser = isUser && i === lastUserIndex;

          return (
            <div
              key={i}
              className={`chat-message-block ${isUser ? "msg-user" : "msg-assistant"}`}
            >
              
              <div className="chat-message-row">
                <div className="chat-message-content">
                  
                  {isUser && <div className="chat-author">user</div>}

                  <div className="chat-bubble">
                    <ReactMarkdown>{m.message}</ReactMarkdown>
                  </div>

                  {isLastUser && editingIndex === null && (
                    <div className="chat-message-actions">
                      <button className="edit-btn" onClick={startEdit}>
                        Edit
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <form className="chat-input-bar" onSubmit={handleSend}>
        <input
          className="chat-input"
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            editingIndex !== null ? "Editing your last message…" : "Ask something."
          }
          disabled={loading}
        />

        {editingIndex !== null && (
          <button
            type="button"
            className="cancel-edit-btn"
            onClick={cancelEdit}
          >
            Cancel
          </button>
        )}

        <button className="chat-send-btn" type="submit" disabled={loading}>
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}
