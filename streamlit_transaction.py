import random

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


def risk_from_amount(amount: float) -> str:
    if amount > 99999:
        return "Blocked"
    if amount > 50000:
        return "High"
    if amount > 10000:
        return "Medium"
    return "Low"


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

        transfer_duration = st.selectbox(
            "Transfer Duration",
            ["Instant (0-10 sec)", "Quick (under 2 min)", "Standard (2-30 min)", "Scheduled"],
        )

        amount = st.number_input("Amount (INR)", min_value=1, step=100, value=1000)

    with right:
        st.info(
            "Rules:\n"
            "- More than INR 99,999: not supported\n"
            "- INR 10,001 to 50,000: medium (OTP required)\n"
            "- INR 50,001 to 99,999: high (warning)\n"
            "- Up to INR 10,000: low"
        )

    tx = {
        "amount": amount,
        "payment_platform": payment_platform,
        "transaction_type": transaction_type,
        "transfer_duration": transfer_duration,
    }
    level = risk_from_amount(amount)
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
            "Warning notification: Large amount transaction detected. Please re-check before confirming."
        )
        st.session_state.pending_medium = None
        st.session_state.otp_code = None
        st.session_state.otp_verified = False
        st.session_state.otp_tx_key = None
        show_transaction_summary(tx, "Yes", "Transaction can proceed with warning notification.")
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
