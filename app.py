import csv
import hashlib
import json
import os
import pickle
import re
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, redirect, render_template, request, session, url_for


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "upi_demo_secret_key_change_me")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

BASE_DIR = Path(__file__).resolve().parent
USER_STORE_PATH = BASE_DIR / "users.json"
FEEDBACK_PATH = BASE_DIR / "feedback.csv"
MODEL_PATH = BASE_DIR / "UPI_Fraud_Detection_Model_Fixed.pkl"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def seed_users() -> dict:
    return {
        "admin@upi.com": {
            "name": "Admin User",
            "email": "admin@upi.com",
            "password_hash": hash_password("admin123"),
        }
    }


def save_users(users: dict) -> None:
    USER_STORE_PATH.write_text(json.dumps(users, indent=2), encoding="utf-8")


def load_users() -> dict:
    if not USER_STORE_PATH.exists():
        users = seed_users()
        save_users(users)
        return users
    try:
        raw = USER_STORE_PATH.read_text(encoding="utf-8")
        data = json.loads(raw) if raw.strip() else {}
        if not isinstance(data, dict):
            raise ValueError("Invalid user store")
        return data
    except Exception:
        users = seed_users()
        save_users(users)
        return users


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def load_artifact():
    if not MODEL_PATH.exists():
        return None
    with MODEL_PATH.open("rb") as f:
        return pickle.load(f)


def probability_to_level(probability: float) -> str:
    if probability <= 0.35:
        return "Low"
    if probability <= 0.70:
        return "Medium"
    return "High"


def score_transaction(artifact: dict, payload: dict) -> float:
    amount = float(payload.get("amount", 0))
    transaction_type = str(payload.get("transaction_type", "P2P Transfer"))
    payment_gateway = str(payload.get("payment_gateway", "PhonePe"))
    device_used = str(payload.get("device_used", "Android"))
    location = str(payload.get("location", "Home State"))
    payment_method = str(payload.get("payment_method", "UPI PIN"))
    time_of_transaction = int(payload.get("time_of_transaction", 12))
    previous_fraud_txn = int(payload.get("previous_fraudulent_transactions", 0))
    account_age = int(payload.get("account_age", 365))
    txn_last_24h = int(payload.get("number_of_transactions_last_24h", 3))

    # Dataset-based pipeline artifact
    if "pipeline" in artifact:
        pipeline = artifact["pipeline"]
        row = pd.DataFrame(
            [
                {
                    "Transaction_Amount": amount,
                    "Transaction_Type": transaction_type,
                    "Time_of_Transaction": time_of_transaction,
                    "Device_Used": device_used,
                    "Location": location,
                    "Previous_Fraudulent_Transactions": previous_fraud_txn,
                    "Account_Age": account_age,
                    "Number_of_Transactions_Last_24H": txn_last_24h,
                    "Payment_Method": payment_method,
                }
            ]
        )
        return float(pipeline.predict_proba(row)[:, 1][0])

    # Legacy notebook artifact support
    feature_columns = artifact.get("feature_columns", [])
    scaler = artifact.get("scaler")
    model = artifact.get("model")
    legacy_row = pd.DataFrame(
        [
            {
                "amount": amount,
                "Transaction_Frequency": txn_last_24h,
                "Transaction_Type": transaction_type,
                "Payment_Gateway": payment_gateway,
                "Merchant_Category": location,
                "Device_OS": device_used,
            }
        ]
    )
    encoded = pd.get_dummies(legacy_row)
    aligned = encoded.reindex(columns=feature_columns, fill_value=0)
    data = scaler.transform(aligned) if scaler is not None else aligned
    if hasattr(model, "predict_proba"):
        return float(model.predict_proba(data)[:, 1][0])
    return float(model.predict(data)[0])


@app.route("/")
def index_page():
    if session.get("authenticated"):
        return redirect(url_for("home_page"))
    return render_template("index.html")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/home")
def home_page():
    if not session.get("authenticated"):
        return redirect(url_for("index_page"))
    return render_template("home.html", username=session.get("name", "User"))


@app.route("/transaction-verification")
def transaction_verification_page():
    if not session.get("authenticated"):
        return redirect(url_for("index_page"))
    return render_template("risk_dashboard.html", username=session.get("name", "User"))


@app.post("/api/login")
def api_login():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))

    users = load_users()
    user = users.get(email)
    if user and user.get("password_hash") == hash_password(password):
        session["authenticated"] = True
        session["email"] = email
        session["name"] = user.get("name", "User")
        return jsonify({"ok": True, "redirect": url_for("home_page")})

    return jsonify({"ok": False, "message": "Invalid email or password."}), 401


@app.post("/api/register")
def api_register():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    confirm_password = str(payload.get("confirm_password", ""))

    if len(name) < 2:
        return jsonify({"ok": False, "message": "Name must be at least 2 characters."}), 400
    if not is_valid_email(email):
        return jsonify({"ok": False, "message": "Please enter a valid email."}), 400
    if len(password) < 6:
        return jsonify({"ok": False, "message": "Password must be at least 6 characters."}), 400
    if password != confirm_password:
        return jsonify({"ok": False, "message": "Passwords do not match."}), 400

    users = load_users()
    if email in users:
        return jsonify({"ok": False, "message": "Email is already registered."}), 400

    users[email] = {
        "name": name,
        "email": email,
        "password_hash": hash_password(password),
    }
    save_users(users)
    return jsonify({"ok": True, "message": "Registration successful. Please login."})


@app.post("/api/logout")
def api_logout():
    session.clear()
    return jsonify({"ok": True})


@app.post("/api/transaction-verification")
def api_transaction_verification():
    if not session.get("authenticated"):
        return jsonify({"ok": False, "message": "Unauthorized"}), 401

    artifact = load_artifact()
    if artifact is None:
        return jsonify({"ok": False, "message": "Model file not found on server."}), 500

    payload = request.get_json(silent=True) or {}
    try:
        amount = float(payload.get("amount", 0))
    except Exception:
        return jsonify({"ok": False, "message": "Invalid amount."}), 400

    if amount > 99999:
        return jsonify(
            {
                "ok": True,
                "level": "High",
                "allowed": False,
                "requires_confirmation": False,
                "message": "High-risk transactions are immediately blocked and secured using advanced verification methods to prevent fraud and protect user funds..",
            }
        )

    probability = score_transaction(artifact, payload)
    level = probability_to_level(probability)
    confirmed = bool(payload.get("confirmed", False))

    if level == "Low":
        return jsonify(
            {
                "ok": True,
                "level": level,
                "allowed": True,
                "requires_confirmation": False,
                "message": "Safe UPI transactions are approved instantly using intelligent machine learning checks, ensuring fast and smooth payments without any user interruption.",
            }
        )
    if level == "Medium":
        if not confirmed:
            return jsonify(
                {
                    "ok": True,
                    "level": level,
                    "allowed": False,
                    "requires_confirmation": True,
                    "message": "Suspicious transactions trigger instant alerts and user confirmation to verify authenticity while minimizing inconvenience...",
                }
            )
        return jsonify(
            {
                "ok": True,
                "level": level,
                "allowed": True,
                "requires_confirmation": False,
                "message": "User confirmation received. Transaction verified and approved.",
            }
        )
    return jsonify(
        {
            "ok": True,
            "level": level,
            "allowed": False,
            "requires_confirmation": False,
            "message": "High-risk transactions are immediately blocked and secured using advanced verification methods to prevent fraud and protect user funds..",
        }
    )


@app.post("/api/feedback")
def api_feedback():
    if not session.get("authenticated"):
        return jsonify({"ok": False, "message": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip()
    suggestions = str(payload.get("suggestions", "")).strip()

    if not name or not email or not suggestions:
        return jsonify({"ok": False, "message": "Please fill all feedback fields."}), 400

    write_header = not FEEDBACK_PATH.exists()
    with FEEDBACK_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["name", "email", "suggestions"])
        writer.writerow([name, email, suggestions])

    return jsonify({"ok": True, "message": "Feedback submitted successfully."})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
