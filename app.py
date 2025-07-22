import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import hashlib
from sqlalchemy import create_engine, text

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="GreenInvest Analytics Dashboard", layout="wide")

# -------------------- STYLING --------------------
st.markdown("""
    <style>
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .welcome-banner {
            animation: fadeInUp 1s ease-out;
        }
        .stApp {
            background: linear-gradient(to right, #c4fda1, #c2e9fb, #cfa1fd);
            animation: gradient 15s ease infinite;
            background-size: 400% 400%;
        }
        @keyframes gradient {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(to bottom, #1e3c72, #2a5298);
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stTabs [data-baseweb="tab"] {
            color: white !important;
        }
        section[data-testid="stSidebar"] .stTabs [aria-selected="true"] {
            font-weight: bold;
            border-bottom: 2px solid #f0b90b;
        }
    </style>
""", unsafe_allow_html=True)

# -------------------- DATABASE SETUP --------------------
user_engine = create_engine('sqlite:///users.db')
feedback_engine = create_engine('sqlite:///feedback.db')

# Create necessary tables
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
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))

# -------------------- AUTH FUNCTIONS --------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    df = pd.read_sql("SELECT * FROM users WHERE username = ?", user_engine, params=(username,))
    return not df.empty and df['password'][0] == hash_password(password)

def register_user(username, password):
    df = pd.read_sql("SELECT * FROM users WHERE username = ?", user_engine, params=(username,))
    if not df.empty:
        return False
    with user_engine.connect() as conn:
        conn.execute(text("INSERT INTO users (username, password) VALUES (:u, :p)"),
                     {"u": username, "p": hash_password(password)})
    return True

def submit_feedback(username, message):
    with feedback_engine.connect() as conn:
        conn.execute(text("INSERT INTO feedback (username, message) VALUES (:u, :m)"),
                     {"u": username, "m": message})

# -------------------- STREAMLIT UI --------------------
st.markdown("""
    <div class="welcome-banner" style="text-align:center; padding: 2rem 1rem;
            border-radius: 15px; background: linear-gradient(to right, #89f7fe, #66a6ff);
            color: #ffffff; font-size: 2.5rem; font-weight: bold;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            box-shadow: 0 0 20px rgba(0,0,0,0.3);">
        🚀 Welcome to the <span style="color: #ffdf00;">✨ GreenInvest Analytics</span>!
    </div>
""", unsafe_allow_html=True)

menu = st.sidebar.selectbox("Menu", ["Login", "Sign Up", "Feedback"])

if menu == "Login":
    st.subheader("Login to Your Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if verify_user(username, password):
            st.success(f"Welcome, {username}!")
        else:
            st.error("Invalid username or password")

elif menu == "Sign Up":
    st.subheader("Create a New Account")
    new_user = st.text_input("New Username")
    new_pass = st.text_input("New Password", type="password")
    if st.button("Sign Up"):
        if register_user(new_user, new_pass):
            st.success("Account created successfully. You can now log in.")
        else:
            st.warning("Username already exists. Try a different one.")

elif menu == "Feedback":
    st.subheader("We'd Love Your Feedback 💬")
    name = st.text_input("Your Name")
    message = st.text_area("Your Message")
    if st.button("Submit Feedback"):
        if name and message:
            submit_feedback(name, message)
            st.success("Thank you for your feedback!")
        else:
            st.warning("Please enter both name and message.")

# -------------------- ESG DASHBOARD FUNCTIONS --------------------
# (Put your ESG functions and UI here – no change needed)
# Your calculate_esg_score(), get_recommendations(), get_financial_opportunities(),
# display_dashboard() functions remain as is from your original code.

# Also include the ESG input method (manual or CSV) and call display_dashboard()

# -------------------- Footer --------------------
st.markdown("---")
st.write("Made with ❤️ for a greener future.")
