const riskForm = document.getElementById("risk-form");
const resultBox = document.getElementById("risk-result");
const riskBadge = document.getElementById("risk-badge");
const resultAmount = document.getElementById("result-amount");
const resultAllowed = document.getElementById("result-allowed");
const resultDecision = document.getElementById("result-decision");

function classForLevel(level) {
  if (level === "Low") return "risk-low";
  if (level === "Medium") return "risk-medium";
  if (level === "High") return "risk-high";
  return "risk-blocked";
}

function badgeStyle(level) {
  if (level === "Low") return { bg: "#dcfce7", fg: "#166534" };
  if (level === "Medium") return { bg: "#fef3c7", fg: "#92400e" };
  if (level === "High") return { bg: "#fee2e2", fg: "#991b1b" };
  return { bg: "#ede9fe", fg: "#5b21b6" };
}

riskForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const amount = Number(document.getElementById("amount").value);

  const response = await fetch("/api/risk-level", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ amount }),
  });
  const data = await response.json();

  if (!response.ok || !data.ok) {
    resultBox.className = "result";
    if (riskBadge && resultAmount && resultAllowed && resultDecision) {
      riskBadge.textContent = "Error";
      resultAmount.textContent = "-";
      resultAllowed.textContent = "-";
      resultDecision.textContent = data.message || "Unable to evaluate amount.";
    }
    resultBox.classList.remove("hidden");
    return;
  }

  resultBox.className = `result ${classForLevel(data.level)}`;
  const style = badgeStyle(data.level);
  riskBadge.textContent = data.level;
  riskBadge.style.backgroundColor = style.bg;
  riskBadge.style.color = style.fg;
  resultAmount.textContent = `INR ${amount.toLocaleString("en-IN")}`;
  resultAllowed.textContent = data.allowed ? "Yes" : "No";
  resultDecision.textContent = data.message;
  resultBox.classList.remove("hidden");
});
