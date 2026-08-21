fetch("https://northstar-one-backend.onrender.com/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message: userMessage }),
});

const header = document.getElementById("site-header");
window.addEventListener("scroll", () => {
  header.classList.toggle("scrolled", window.scrollY > 40);
});

function getSessionId() {
  return crypto.randomUUID
    ? crypto.randomUUID()
    : "sess-" + Date.now() + "-" + Math.random().toString(16).slice(2);
}
const SESSION_ID = getSessionId();

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

async function startConversation() {
  showTyping();
  try {
    const res = await fetch(`${API_BASE}/start/${SESSION_ID}`, {
      method: "POST",
    });
    const data = await res.json();
    hideTyping();
    const msgs = data.messages || [];
    for (let i = 0; i < msgs.length; i++) {
      if (i > 0) {
        showTyping();
        await new Promise((r) => setTimeout(r, 700));
        hideTyping();
      }
      appendMessage(msgs[i], "bot");
    }
  } catch (err) {
    hideTyping();
    appendMessage(
      "Couldn't reach the server. Is the backend running on " + API_BASE + "?",
      "bot",
    );
    console.error(err);
  }
}

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
    const reply =
      (data.reply && data.reply.trim()) ||
      data.response ||
      data.message ||
      "Sorry, something went wrong on my end — could you try that again?";
    appendMessage(reply, "bot");
    if (data.conversation_ended) endConversationUI();
  } catch (err) {
    hideTyping();
    appendMessage(
      "Couldn't reach the server. Is the backend running on " + API_BASE + "?",
      "bot",
    );
    console.error(err);
  }
}

function endConversationUI() {
  chatInput.disabled = true;
  chatSend.disabled = true;
  chatInput.placeholder = "Conversation ended";
  if (micBtn) micBtn.disabled = true;

  const divider = document.createElement("div");
  divider.className = "chat-ended-divider";
  divider.textContent = "Conversation ended";
  chatLog.appendChild(divider);

  const restartBtn = document.createElement("button");
  restartBtn.type = "button";
  restartBtn.className = "chat-restart-btn";
  restartBtn.textContent = "Start New Conversation";
  restartBtn.addEventListener("click", restartConversation);
  chatLog.appendChild(restartBtn);
  chatLog.scrollTop = chatLog.scrollHeight;
  setTimeout(closeChat, 2000);
}

async function restartConversation() {
  try {
    await fetch(`${API_BASE}/reset/${SESSION_ID}`, { method: "POST" });
  } catch (err) {
    console.error(err);
  }
  chatLog.innerHTML = "";
  chatInput.disabled = false;
  chatSend.disabled = false;
  chatInput.placeholder = "Ask about a 2 BHK, pricing, availability…";
  if (micBtn && recognition) micBtn.disabled = false;
  startConversation();
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

window.addEventListener("load", () => {
  setTimeout(() => {
    openChat();
    chatBadge.classList.add("show");
    startConversation();
  }, 5000);
});

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

const micBtn = document.getElementById("chat-mic");
const langToggle = document.getElementById("mic-lang-toggle");

const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let isListening = false;
let voiceLang = "en-IN";

if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    chatInput.value = transcript;
    chatInput.focus();
  };
  recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
    stopListeningUI();
    if (event.error === "not-allowed" || event.error === "permission-denied") {
      appendMessage(
        "Mic access was blocked — allow microphone permission in your browser to use voice input.",
        "bot",
      );
    }
  };
  recognition.onend = () => stopListeningUI();
} else if (micBtn) {
  micBtn.disabled = true;
  micBtn.title =
    "Voice input isn't supported in this browser — try Chrome or Edge.";
}

function startListeningUI() {
  isListening = true;
  micBtn.classList.add("listening");
}
function stopListeningUI() {
  isListening = false;
  if (micBtn) micBtn.classList.remove("listening");
}

micBtn?.addEventListener("click", () => {
  if (!recognition) return;
  if (isListening) {
    recognition.stop();
    return;
  }
  recognition.lang = voiceLang;
  startListeningUI();
  try {
    recognition.start();
  } catch (err) {
    console.error(err);
    stopListeningUI();
  }
});

langToggle?.addEventListener("click", () => {
  voiceLang = voiceLang === "en-IN" ? "hi-IN" : "en-IN";
  langToggle.textContent = voiceLang === "en-IN" ? "EN" : "हि";
});
