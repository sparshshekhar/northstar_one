// ---------- config ----------
const API_BASE = "http://127.0.0.1:8000"; // change if your backend runs elsewhere

// ---------- header scroll state ----------
const header = document.getElementById("site-header");
window.addEventListener("scroll", () => {
  header.classList.toggle("scrolled", window.scrollY > 40);
});

// ---------- session id ----------
function getSessionId() {
  let id = sessionStorage.getItem("northstar_session_id");
  if (!id) {
    id = crypto.randomUUID
      ? crypto.randomUUID()
      : "sess-" + Date.now() + "-" + Math.random().toString(16).slice(2);
    sessionStorage.setItem("northstar_session_id", id);
  }
  return id;
}
const SESSION_ID = getSessionId();

// ---------- chat widget elements ----------
const chatLauncher = document.getElementById("chat-launcher");
const chatBadge = document.getElementById("chat-badge");
const chatPanel = document.getElementById("chat-panel");
const chatClose = document.getElementById("chat-close");
const chatLog = document.getElementById("chat-log");
const chatInput = document.getElementById("chat-input");
const chatSend = document.getElementById("chat-send");

function openChat() {
  chatPanel.classList.add("open");
  chatBadge.classList.remove("show");
}
function closeChat() {
  chatPanel.classList.remove("open");
}
chatLauncher.addEventListener("click", () => {
  chatPanel.classList.contains("open") ? closeChat() : openChat();
});
chatClose.addEventListener("click", closeChat);

function appendMessage(text, who) {
  const div = document.createElement("div");
  div.className = "msg " + who;
  div.textContent = text;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
  return div;
}

function showTyping() {
  const div = document.createElement("div");
  div.className = "msg typing";
  div.textContent = "Typing…";
  div.id = "typing-indicator";
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
}
function hideTyping() {
  const el = document.getElementById("typing-indicator");
  if (el) el.remove();
}

// Sends a message to the backend. If hideUserBubble is true, the user's
// message is sent but not rendered — used for the automatic opening greeting.
async function sendToBackend(message, { hideUserBubble = false } = {}) {
  if (!hideUserBubble) appendMessage(message, "user");
  showTyping();
  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: SESSION_ID, message }),
    });
    const data = await res.json();
    hideTyping();
    // Adjust this if your /chat response uses a different field name
    const reply =
      (data.reply && data.reply.trim()) ||
      data.response ||
      data.message ||
      "Sorry, something went wrong on my end — could you try that again?";
    appendMessage(reply, "bot");
  } catch (err) {
    hideTyping();
    appendMessage(
      "Couldn't reach the server. Is the backend running on " + API_BASE + "?",
      "bot",
    );
    console.error(err);
  }
}

chatSend.addEventListener("click", () => {
  const text = chatInput.value.trim();
  if (!text) return;
  chatInput.value = "";
  sendToBackend(text);
});
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") chatSend.click();
});

// ---------- auto-start after 5 seconds ----------
window.addEventListener("load", () => {
  setTimeout(() => {
    openChat();
    chatBadge.classList.add("show");
    // Kicks off the conversation with a hidden trigger message —
    // only the bot's reply is shown, so it reads as the bot greeting first.
    sendToBackend("Hi", { hideUserBubble: true });
  }, 5000);
});

// ---------- booking form ----------
const bookForm = document.getElementById("book-form");
const bookResult = document.getElementById("book-result");

bookForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    session_id: SESSION_ID,
    configuration: document.getElementById("bf-config").value,
    preferred_date: document.getElementById("bf-date").value,
    preferred_time: document.getElementById("bf-time").value,
    contact_number: document.getElementById("bf-phone").value,
  };

  bookResult.className = "show";
  bookResult.textContent = "Checking availability…";

  try {
    const res = await fetch(`${API_BASE}/book-visit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    bookResult.className = "show" + (data.status === "failed" ? " failed" : "");
    bookResult.textContent = data.message || JSON.stringify(data);
  } catch (err) {
    bookResult.className = "show failed";
    bookResult.textContent =
      "Couldn't reach the server. Is the backend running on " + API_BASE + "?";
    console.error(err);
  }
});
