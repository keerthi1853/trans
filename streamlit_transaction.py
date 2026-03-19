import streamlit as st
import random


st.set_page_config(page_title="UPI Transaction Page", page_icon=":money_with_wings:", layout="centered")

if "otp_code" not in st.session_state:
    st.session_state.otp_code = None
if "pending_medium" not in st.session_state:
    st.session_state.pending_medium = None

top_notice = st.empty()

st.title("UPI Transaction")
st.caption("Choose payment details and validate transfer amount")

st.markdown("### Transaction Details")

payment_platform = st.selectbox(
    "Select Paying Platform",
    ["Google Pay", "PhonePe", "Paytm", "BHIM", "Amazon Pay", "Bank UPI App"],
)

transaction_type = st.selectbox(
    "Select Transaction Type",
    ["P2P Transfer", "P2M Payment", "Bill Payment", "Recharge", "Subscription"],
)

transfer_duration = st.selectbox(
    "Select Transfer Time Duration",
    ["Instant (0-10 sec)", "Quick (under 2 min)", "Standard (2-30 min)", "Scheduled"],
)

amount = st.number_input("Enter Amount (INR)", min_value=1, step=100, value=1000)


def show_summary(risk_level: str) -> None:
    st.markdown(f"**Amount:** INR {amount:,.0f}")
    st.markdown(f"**Platform:** {payment_platform}")
    st.markdown(f"**Transaction Type:** {transaction_type}")
    st.markdown(f"**Transfer Duration:** {transfer_duration}")
    st.markdown(f"**Risk Level:** {risk_level}")


if st.button("Proceed Transaction"):
    if amount > 99999:
        st.error(
            "This account does not support transferring more than INR 99,999. "
            "Please enter a lower amount."
        )
        st.session_state.pending_medium = None
        st.session_state.otp_code = None
    else:
        if amount <= 10000:
            st.success("Transaction request accepted.")
            show_summary("Low")
            st.session_state.pending_medium = None
            st.session_state.otp_code = None
        elif amount <= 50000:
            otp_code = str(random.randint(100000, 999999))
            st.session_state.otp_code = otp_code
            st.session_state.pending_medium = {
                "amount": amount,
                "payment_platform": payment_platform,
                "transaction_type": transaction_type,
                "transfer_duration": transfer_duration,
            }
            top_notice.info("Medium risk transaction detected. OTP sent for verification.")
            st.info("Enter OTP to allow the transaction. Without OTP verification, transaction is stopped.")
            st.caption(f"Demo OTP: {otp_code}")
        else:
            top_notice.warning(
                "Warning: High risk transaction detected. Please verify details before proceeding."
            )
            st.success("Transaction request accepted with warning.")
            show_summary("High")
            st.session_state.pending_medium = None
            st.session_state.otp_code = None

if st.session_state.pending_medium:
    st.markdown("---")
    st.subheader("OTP Verification")
    entered_otp = st.text_input("Enter 6-digit OTP", max_chars=6)

    if st.button("Verify OTP"):
        if entered_otp == st.session_state.otp_code:
            st.success("OTP verified. Transaction allowed.")
            pending = st.session_state.pending_medium
            st.markdown(f"**Amount:** INR {pending['amount']:,.0f}")
            st.markdown(f"**Platform:** {pending['payment_platform']}")
            st.markdown(f"**Transaction Type:** {pending['transaction_type']}")
            st.markdown(f"**Transfer Duration:** {pending['transfer_duration']}")
            st.markdown("**Risk Level:** Medium")
            st.session_state.pending_medium = None
            st.session_state.otp_code = None
        else:
            st.error("Invalid OTP. Transaction stopped.")
