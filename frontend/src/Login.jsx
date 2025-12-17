import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "./api";
import "./Auth.css";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
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
  const isValidBinusEmail = (email) =>
    /^[^\s@]+@binus\.ac\.id$/i.test(email);

  
  const handleSubmit = async (e) => {
  e.preventDefault();
  setError("");

  if (!isValidBinusEmail(email)) {
    setError("Please use your BINUS email (@binus.ac.id).");
    return;
  }

  try {
    setLoading(true);
    await api.login(email, password);
    onLogin();
    navigate("/");
  } catch (err) {
    setError("Invalid email or password");
  } finally {
    setLoading(false);
  }
};


  return (
    <div className="auth-page">
      <div className="auth-bg" />

      <div className="auth-card">
        <h1 className="auth-title">Welcome Back</h1>
        <p className="auth-subtitle">Sign in to continue</p>

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
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>

        <div className="auth-footer">
          Don’t have an account?{" "}
          <span className="auth-link" onClick={() => navigate("/register")}>
            Register
          </span>
        </div>
      </div>
    </div>
  );
}
