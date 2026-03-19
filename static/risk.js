const riskForm = document.getElementById("risk-form");
const resultBox = document.getElementById("risk-result");
const riskBadge = document.getElementById("risk-badge");
const resultAmount = document.getElementById("result-amount");
const resultAllowed = document.getElementById("result-allowed");
const resultDecision = document.getElementById("result-decision");

function classForLevel(level) {
  if (level === "Low") return "risk-low";
  if (level === "Medium") return "risk-medium";
  return "risk-high";
}

riskForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    amount: Number(document.getElementById("amount").value),
    transaction_type: document.getElementById("transaction-type").value,
    payment_gateway: document.getElementById("payment-gateway").value,
    device_used: document.getElementById("device-used").value,
    location: document.getElementById("location").value,
    payment_method: document.getElementById("payment-method").value,
    time_of_transaction: Number(document.getElementById("time-of-transaction").value),
    previous_fraudulent_transactions: Number(
      document.getElementById("previous-fraudulent-transactions").value
    ),
    account_age: Number(document.getElementById("account-age").value),
    number_of_transactions_last_24h: Number(
      document.getElementById("number-of-transactions-last-24h").value
    ),
    confirmed: document.getElementById("confirmed").checked,
  };

  const response = await fetch("/api/transaction-verification", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();

  if (!response.ok || !data.ok) {
    resultBox.className = "result";
    riskBadge.textContent = "Error";
    resultAmount.textContent = "-";
    resultAllowed.textContent = "-";
    resultDecision.textContent = data.message || "Unable to verify transaction.";
    resultBox.classList.remove("hidden");
    return;
  }

  resultBox.className = `result ${classForLevel(data.level)}`;
  riskBadge.textContent = data.level;
  resultAmount.textContent = `INR ${payload.amount.toLocaleString("en-IN")}`;
  resultAllowed.textContent = data.allowed ? "Yes" : "No";
  resultDecision.textContent = data.message;
  resultBox.classList.remove("hidden");
});
