import React from "react";
import "./ConfirmModal.css";  

export default function ConfirmModal({ open, title, message, onCancel, onConfirm }) {
  if (!open) return null;

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal-panel" role="document">
        <header className="modal-header">
          <h3>{title || "Confirm"}</h3>
        </header>

        <div className="modal-body">
          <p>{message}</p>
        </div>

        <footer className="modal-footer">
          <button className="btn btn-secondary" onClick={onCancel}>Cancel</button>
          <button className="btn btn-primary" onClick={onConfirm}>OK</button>
        </footer>
      </div>
    </div>
  );
}
