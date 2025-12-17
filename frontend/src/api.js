import axios from "axios";

const API_URL = "http://localhost:8000";

function getToken() {
  return localStorage.getItem("access_token");
}

const client = axios.create({
  baseURL: API_URL,
});


client.interceptors.request.use((config) => {
  const token = getToken();
  console.log("[api] request:", config.method?.toUpperCase(), config.url, "tokenPresent:", !!token);
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (err) => Promise.reject(err));

export const api = {
  register: async (username, password) => {
    const res = await client.post("/register", { username, password });
    return res.data;
  },

  login: async (username, password) => {
    const body = new URLSearchParams();
    body.append("username", username);
    body.append("password", password);
    const res = await client.post("/token", body.toString(), {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    localStorage.setItem("access_token", res.data.access_token);
    return res.data;
  },

  logout: () => {
    localStorage.removeItem("access_token");
  },


  getSessions: async () => {
    const res = await client.get("/sessions");
    return res.data;
  },

  createSession: async (topic) => {
    const res = await client.post("/session", { topic });
    return res.data;
  },

getHistory: async (sessionId) => {
  const res = await client.get(`/history/${sessionId}`);
  console.log("[api] getHistory res:", res);
  return res;
},

sendMessage: async (sessionId, message) => {
  const res = await client.post(`/chat/${sessionId}`, {
    user_input: message,
  });
  console.log("[api] sendMessage res:", res);
  return res; 
},

  editLastMessage: async (sessionId, newMessage) => {
    const res = await client.post(`/chat/${sessionId}/edit_last`, { user_input: newMessage });
    return res;
  },

  deleteSession: async (sessionId) => {
    const res = await client.delete(`/session/${sessionId}`);
    return res.data;
  },
};
