import React from "react";
import "./Modal.css";

export default function SuccessModal({ open, title, message, onClose }) {
  if (!open) return null;

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal-panel">
        <header className="modal-header">
          <h3>{title || "Success"}</h3>
        </header>

        <div className="modal-body">
          <p>{message}</p>
        </div>

        <footer className="modal-footer">
          <button className="btn btn-primary" onClick={onClose}>
            OK
          </button>
        </footer>
      </div>
    </div>
  );
}
