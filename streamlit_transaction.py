import random
import pickle
from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="UPI Shield Dashboard",
    page_icon=":shield:",
    layout="wide",
)


if "otp_code" not in st.session_state:
    st.session_state.otp_code = None
if "pending_medium" not in st.session_state:
    st.session_state.pending_medium = None
if "otp_verified" not in st.session_state:
    st.session_state.otp_verified = False
if "otp_tx_key" not in st.session_state:
    st.session_state.otp_tx_key = None


MODEL_PATH = Path(__file__).resolve().parent / "UPI_Fraud_Detection_Model_Fixed.pkl"


@st.cache_resource(show_spinner=False)
def load_model_artifact():
    if not MODEL_PATH.exists():
        return None
    with MODEL_PATH.open("rb") as f:
        return pickle.load(f)


def probability_to_bucket(probability: float) -> str:
    if probability <= 0.35:
        return "Low"
    if probability <= 0.70:
        return "Medium"
    return "High"


def score_with_model(artifact: dict, tx: dict) -> float:
    # New artifact format: sklearn pipeline trained on upi_fraud_dataset.csv
    if "pipeline" in artifact:
        pipeline = artifact["pipeline"]
        row = pd.DataFrame(
            [
                {
                    "Transaction_Amount": float(tx["amount"]),
                    "Transaction_Type": tx["transaction_type"],
                    "Time_of_Transaction": int(tx["time_of_transaction"]),
                    "Device_Used": tx["device_used"],
                    "Location": tx["location"],
                    "Previous_Fraudulent_Transactions": int(tx["previous_fraud_txn"]),
                    "Account_Age": int(tx["account_age"]),
                    "Number_of_Transactions_Last_24H": int(tx["txn_last_24h"]),
                    "Payment_Method": tx["payment_method"],
                }
            ]
        )
        probability = float(pipeline.predict_proba(row)[:, 1][0])
        return max(0.0, min(1.0, probability))

    # Legacy artifact support
    feature_columns = artifact.get("feature_columns", [])
    scaler = artifact.get("scaler")
    model = artifact.get("model")
    row = pd.DataFrame(
        [
            {
                "amount": float(tx["amount"]),
                "Transaction_Frequency": float(tx["txn_last_24h"]),
                "Transaction_Type": tx["transaction_type"],
                "Payment_Gateway": tx["payment_platform"],
                "Merchant_Category": tx["location"],
                "Device_OS": tx["device_used"],
            }
        ]
    )
    encoded = pd.get_dummies(row)
    aligned = encoded.reindex(columns=feature_columns, fill_value=0)
    data = scaler.transform(aligned) if scaler is not None else aligned
    probability = (
        float(model.predict_proba(data)[:, 1][0])
        if hasattr(model, "predict_proba")
        else float(model.predict(data)[0])
    )
    return max(0.0, min(1.0, probability))


def tx_key(data: dict) -> str:
    return (
        f"{data['amount']}|{data['payment_platform']}|"
        f"{data['transaction_type']}|{data['transfer_duration']}"
    )


def show_transaction_summary(data: dict, transfer_allowed_text: str, decision_text: str) -> None:
    a, b = st.columns(2)
    with a:
        st.markdown(f"**Amount:** INR {data['amount']:,.0f}")
        st.markdown(f"**Platform:** {data['payment_platform']}")
    with b:
        st.markdown(f"**Type:** {data['transaction_type']}")
        st.markdown(f"**Duration:** {data['transfer_duration']}")
    st.markdown(f"**Transfer Allowed:** {transfer_allowed_text}")
    st.markdown(f"**Decision:** {decision_text}")


st.title("UPI Shield Dashboard")
top_notice = st.empty()

artifact = load_model_artifact()
if artifact is None:
    st.error(
        "Model file not found: UPI_Fraud_Detection_Model_Fixed.pkl. "
        "Place this file in the trans folder and refresh."
    )
    st.stop()

tab1, tab2 = st.tabs(["Main Page", "Risk Scoring"])

with tab1:
    st.subheader("Mission")
    st.write(
        "Deliver secure and reliable UPI transactions with smart protection, "
        "better user trust, and fast payment experiences."
    )

    st.subheader("Vision")
    st.write(
        "Build a safe digital payment ecosystem where every transfer is protected "
        "with clear risk checks and guided verification."
    )

    st.subheader("Services")
    st.markdown(
        "- Secure transaction risk evaluation\n"
        "- OTP-based verification for medium-risk transfers\n"
        "- Automatic warning notifications for high-risk transfers"
    )

with tab2:
    st.subheader("Transaction Check")

    left, right = st.columns([2, 1])

    with left:
        payment_platform = st.selectbox(
            "Paying Platform",
            ["Google Pay", "PhonePe", "Paytm", "BHIM", "Amazon Pay", "Bank UPI App"],
        )

        transaction_type = st.selectbox(
            "Type of Transaction",
            ["P2P Transfer", "P2M Payment", "Bill Payment", "Recharge", "Subscription"],
        )

        device_used = st.selectbox(
            "Device Used",
            ["Android", "iOS", "Web"],
        )

        location = st.selectbox(
            "Location",
            ["Home State", "Different State", "International"],
        )

        transfer_duration = st.selectbox(
            "Transfer Duration",
            ["Instant (0-10 sec)", "Quick (under 2 min)", "Standard (2-30 min)", "Scheduled"],
        )

        time_of_transaction = st.slider("Hour of Transaction", 0, 23, 12)
        previous_fraud_txn = st.number_input(
            "Previous Fraudulent Transactions", min_value=0, max_value=20, value=0, step=1
        )
        account_age = st.number_input(
            "Account Age (days)", min_value=1, max_value=5000, value=365, step=1
        )
        txn_last_24h = st.number_input(
            "Number of Transactions in Last 24H", min_value=0, max_value=200, value=3, step=1
        )

        amount = st.number_input("Amount (INR)", min_value=1, step=100, value=1000)

    with right:
        st.info(
            "Rules:\n"
            "- More than INR 99,999: not supported\n"
            "- ML model predicts transaction risk\n"
            "- Medium output: OTP required\n"
            "- High output: warning notification"
        )

    tx = {
        "amount": amount,
        "payment_platform": payment_platform,
        "payment_method": "UPI PIN" if payment_platform != "Bank UPI App" else "Biometric",
        "transaction_type": transaction_type,
        "device_used": device_used,
        "location": location,
        "transfer_duration": transfer_duration,
        "time_of_transaction": time_of_transaction,
        "previous_fraud_txn": previous_fraud_txn,
        "account_age": account_age,
        "txn_last_24h": txn_last_24h,
    }
    if amount > 99999:
        level = "Blocked"
    else:
        probability = score_with_model(artifact, tx)
        level = probability_to_bucket(probability)
    current_tx_key = tx_key(tx)

    if level == "Blocked":
        top_notice.error("This account does not support transferring more than INR 99,999.")
        st.session_state.pending_medium = None
        st.session_state.otp_code = None
        st.session_state.otp_verified = False
        st.session_state.otp_tx_key = None
        show_transaction_summary(
            tx,
            "No (Not possible)",
            "Transfer above INR 99,999 is not possible.",
        )
    elif level == "High":
        top_notice.warning(
            "Warning notification: High-risk transaction detected by ML model."
        )
        st.session_state.pending_medium = None
        st.session_state.otp_code = None
        st.session_state.otp_verified = False
        st.session_state.otp_tx_key = None
        show_transaction_summary(
            tx,
            "Yes",
            "Transaction can proceed with warning notification.",
        )
    elif level == "Low":
        top_notice.success("Transaction is within normal range.")
        st.session_state.pending_medium = None
        st.session_state.otp_code = None
        st.session_state.otp_verified = False
        st.session_state.otp_tx_key = None
        show_transaction_summary(tx, "Yes", "Transaction can proceed.")
    else:
        top_notice.info("OTP verification required for this transaction.")

        if st.session_state.otp_tx_key != current_tx_key:
            st.session_state.otp_verified = False

        if st.session_state.otp_verified and st.session_state.otp_tx_key == current_tx_key:
            show_transaction_summary(tx, "Yes", "OTP verified. Transaction can proceed.")
        else:
            show_transaction_summary(tx, "No (OTP required)", "Enter OTP to allow transaction.")

            send_otp = st.button("Send OTP", use_container_width=True)
            if send_otp:
                otp_code = str(random.randint(100000, 999999))
                st.session_state.otp_code = otp_code
                st.session_state.pending_medium = tx
                st.session_state.otp_tx_key = current_tx_key
                st.session_state.otp_verified = False
            if st.session_state.otp_code and st.session_state.otp_tx_key == current_tx_key:
                st.caption(f"Demo OTP: {st.session_state.otp_code}")

    if (
        st.session_state.pending_medium
        and st.session_state.otp_tx_key == current_tx_key
        and not st.session_state.otp_verified
    ):
        st.markdown("---")
        st.markdown("### OTP Verification")
        entered_otp = st.text_input("Enter 6-digit OTP", max_chars=6)
        verify = st.button("Verify OTP", use_container_width=True)

        if verify:
            if entered_otp == st.session_state.otp_code:
                st.success("OTP verified. Transaction allowed.")
                st.session_state.otp_verified = True
            else:
                st.error("Invalid OTP. Transaction stopped.")
                st.session_state.otp_verified = False
