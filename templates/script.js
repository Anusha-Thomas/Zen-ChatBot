// frontend/script.js
const API_BASE = "http://127.0.0.1:8000";

const bubble = document.getElementById("chatBubble");
const chatWindow = document.getElementById("chatWindow");
const closeBtn = document.getElementById("closeBtn");
const messages = document.getElementById("messages");
const sendBtn = document.getElementById("sendBtn");
const userInput = document.getElementById("userInput");

const formPopup = document.getElementById("formPopup");
const contactForm = document.getElementById("contactForm");
const closeForm = document.getElementById("closeForm");

// create user on load
let user_id = localStorage.getItem("zen_user_id");
if (!user_id) {
  fetch(`${API_BASE}/create_user`).then(r => r.json()).then(d => {
    user_id = d.user_id;
    localStorage.setItem("zen_user_id", user_id);
  });
}

bubble.addEventListener("click", () => {
  chatWindow.classList.toggle("hidden");
});

closeBtn.addEventListener("click", () => {
  chatWindow.classList.add("hidden");
});

function addMessage(sender, text) {
  const div = document.createElement("div");
  div.className = `msg ${sender}`;
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

// send chat
sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keypress", (e) => { if (e.key === "Enter") sendMessage(); });

function sendMessage() {
  const question = userInput.value.trim();
  if (!question) return;
  addMessage("user", question);
  userInput.value = "";

  fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ user_id, question })
  })
  .then(res => res.json())
  .then(data => {
    const answer = data.answer || "Sorry, couldn't fetch the answer.";
    addMessage("bot", answer);

    if (data.show_form) {
      // auto-open form
      openFormPopup(question);
    }
  })
  .catch(err => {
    console.error(err);
    addMessage("bot", "Server error. Try again.");
  });
}

// form popup logic
function openFormPopup(triggered_question = "") {
  formPopup.classList.remove("hidden");
  // store triggered question to include with submission
  formPopup.dataset.trigger = triggered_question;
}

closeForm.addEventListener("click", () => {
  formPopup.classList.add("hidden");
});

contactForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const name = document.getElementById("name").value.trim();
  const phone = document.getElementById("phone").value.trim();
  const email = document.getElementById("email").value.trim();
  const course = document.getElementById("course").value.trim();
  const triggered = formPopup.dataset.trigger || "";

  fetch(`${API_BASE}/save_contact`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ user_id, name, phone, email, course, triggered_question: triggered })
  })
  .then(res => res.json())
  .then(resp => {
    addMessage("bot", "Thank you! We have saved your details. Our team will contact you soon.");
    formPopup.classList.add("hidden");
    contactForm.reset();
  })
  .catch(err => {
    console.error(err);
    addMessage("bot", "Failed to save form - please try again.");
  });
});
