import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "./api";
import "./Auth.css";
import SuccessModal from "./SuccessModal";

export default function Register({ onRegister }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [successOpen, setSuccessOpen] = useState(false); 

  const navigate = useNavigate();

  useEffect(() => {
    const bg = document.querySelector(".auth-bg");
    if (!bg) return;

    const handleMouseMove = (e) => {
      const x = (e.clientX / window.innerWidth - 0.5) * 60;
      const y = (e.clientY / window.innerHeight - 0.5) * 60;
      bg.style.transform = `translate(${x}px, ${y}px)`;
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  const isValidEmail = (email) =>
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

  const isValidBinusEmail = (email) =>
    /^[^\s@]+@binus\.ac\.id$/i.test(email);

  const isValidPassword = (password) =>
    password.length >= 8 &&
    /[A-Z]/.test(password) &&
    /[a-z]/.test(password) &&
    /\d/.test(password) &&
    /[!@#$%^&*]/.test(password);

  const handleSubmit = async (e) => {
  e.preventDefault();
  setError("");

  if (!isValidEmail(email)) {
    setError("Please enter a valid email address.");
    return;
  }

  if (!isValidBinusEmail(email)) {
    setError("Registration requires a BINUS email (@binus.ac.id).");
    return;
  }

  if (!isValidPassword(password)) {
    setError(
      "Password must be at least 8 characters and include uppercase, lowercase, number, and special character."
    );
    return;
  }

  try {
    setLoading(true);
    await api.register(email, password);

    setSuccessOpen(true);
  } catch (err) {
    setError("Registration failed. Email may already be in use.");
  } finally {
    setLoading(false);
  }
};

  const handleSuccessClose = () => {
    setSuccessOpen(false);
    navigate("/login");
  };

  return (
    <div className="auth-page">
      <div className="auth-bg" />

      <div className="auth-card">
        <h1 className="auth-title">Create Account</h1>
        <p className="auth-subtitle">Sign up to get started</p>

        {error && <div className="auth-error">{error}</div>}

        <form className="auth-form" onSubmit={handleSubmit}>
          <div>
            <label className="auth-label">Email</label>
            <input
              className="auth-input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="auth-label">Password</label>
            <input
              className="auth-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button className="auth-button" type="submit" disabled={loading}>
            {loading ? "Creating account..." : "Register"}
          </button>
        </form>

        <div className="auth-footer">
          Already have an account?{" "}
          <span className="auth-link" onClick={() => navigate("/login")}>
            Login
          </span>
        </div>
      </div>

      
      <SuccessModal
        open={successOpen}
        title="Account Created 🎉"
        message="Your account has been created successfully. You can now log in."
        onClose={handleSuccessClose}
      />
    </div>
  );
}
