import streamlit as st
import pandas as pd
import hashlib
from sqlalchemy import create_engine, text

# -------------------- CONFIG --------------------
st.set_page_config(page_title="GreenInvest Analytics Dashboard", layout="wide")

# -------------------- DATABASE ENGINES --------------------
user_engine = create_engine('sqlite:///users.db')
feedback_engine = create_engine('sqlite:///feedback.db')

# -------------------- TABLE CREATION --------------------
with user_engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """))

with feedback_engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """))

# -------------------- HELPER FUNCTIONS --------------------
def hash_password(password):
    return hashlib.sha256(password.strip().encode()).hexdigest()

def register_user(username, password):
    username = username.strip()
    password = password.strip()
    df = pd.read_sql("SELECT 1 FROM users WHERE username = ?", user_engine, params=(username,))
    if not df.empty:
        return False  # Username exists
    with user_engine.connect() as conn:
        conn.execute(text("INSERT INTO users (username, password) VALUES (:u, :p)"),
                     {"u": username, "p": hash_password(password)})
    return True

def verify_user(username, password):
    username = username.strip()
    password = password.strip()
    df = pd.read_sql("SELECT password FROM users WHERE username = ?", user_engine, params=(username,))
    if df.empty:
        return False
    return df['password'][0] == hash_password(password)

# -------------------- SESSION SETUP --------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# -------------------- MAIN --------------------
st.title("🌱 GreenInvest Analytics Dashboard")

if not st.session_state.logged_in:
    menu = st.radio("Choose an option", ["Login", "Register"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button(menu):
        if menu == "Register":
            if register_user(username, password):
                st.success("Registration successful! Please login.")
            else:
                st.error("Username already exists. Try a different one.")
        elif menu == "Login":
            if verify_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username.strip()
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

else:
    st.sidebar.success(f"Logged in as: {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # -------------------- DASHBOARD CONTENT --------------------
    st.subheader("📊 Dashboard Section")
    st.info("This is where your investment analysis, charts, uploads, or KPIs would go.")

    # -------------------- FEEDBACK SUBMISSION --------------------
    st.markdown("---")
    st.subheader("💬 Send us your feedback")
    feedback_input = st.text_area("Your message:")
    if st.button("Submit Feedback"):
        if feedback_input.strip() != "":
            with feedback_engine.connect() as conn:
                conn.execute(text("INSERT INTO feedback (username, message) VALUES (:u, :m)"),
                             {"u": st.session_state.username, "m": feedback_input.strip()})
            st.success("Thank you! Feedback submitted.")
        else:
            st.warning("Feedback message cannot be empty.")

    # -------------------- FEEDBACK DISPLAY --------------------
    st.markdown("---")
    st.subheader("📋 All Submitted Feedback")
    with feedback_engine.connect() as conn:
        feedback_df = pd.read_sql("SELECT * FROM feedback ORDER BY timestamp DESC", conn)
    st.dataframe(feedback_df, use_container_width=True)
