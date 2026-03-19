const logoutBtn = document.getElementById("logout-btn");

if (logoutBtn) {
  logoutBtn.addEventListener("click", async () => {
    await fetch("/api/logout", { method: "POST" });
    window.location.href = "/";
  });
}

const feedbackForm = document.getElementById("feedback-form");
const feedbackMessage = document.getElementById("feedback-message");

if (feedbackForm && feedbackMessage) {
  feedbackForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      name: document.getElementById("feedback-name").value.trim(),
      email: document.getElementById("feedback-email").value.trim(),
      suggestions: document.getElementById("feedback-suggestions").value.trim(),
    };

    const response = await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (response.ok && data.ok) {
      feedbackMessage.textContent = data.message;
      feedbackMessage.className = "message success";
      feedbackForm.reset();
      return;
    }
    feedbackMessage.textContent = data.message || "Failed to submit feedback.";
    feedbackMessage.className = "message error";
  });
}
