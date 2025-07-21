import streamlit as st
import pandas as pd

# -------------------- Page Configuration --------------------
st.set_page_config(page_title="GreenInvest Analytics", page_icon="🌱", layout="wide")

# -------------------- Sidebar --------------------
with st.sidebar:
    st.title("📊 About GreenInvest")
    st.markdown("""
    GreenInvest Analytics empowers **SMEs** to measure and improve their **ESG performance**.
    
    🟢 Input operational data  
    🟢 Get automated ESG scores  
    🟢 Receive tailored sustainability advice  
    🟢 Discover green finance opportunities  
    """)
    st.markdown("---")
    st.markdown("Made with ❤️ by Deepak Raj")

# -------------------- Main Title --------------------
st.markdown("<h1 style='text-align: center;'>🌿 GreenInvest Analytics</h1>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align: center; color: grey;'>Helping SMEs Achieve Sustainability & Attract Green Capital</h5>", unsafe_allow_html=True)

st.markdown("---")

# -------------------- ESG Input Form --------------------
st.subheader("📥 ESG Data Input")

with st.form("esg_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        energy_consumption = st.number_input("🔌 Energy Consumption (kWh/month)", min_value=0.0)
    with col2:
        waste_generated = st.number_input("🗑️ Waste Generated (kg/month)", min_value=0.0)
    with col3:
        water_usage = st.number_input("🚰 Water Usage (liters/month)", min_value=0.0)

    submitted = st.form_submit_button("📊 Calculate ESG Score")

# -------------------- ESG Score Calculation --------------------
def calculate_esg_score(energy, waste, water):
    score = 100 - (energy * 0.03 + waste * 0.04 + water * 0.02)
    return max(min(score, 100), 0)

def get_recommendations(energy, waste, water):
    recs = []
    if energy > 1000:
        recs.append("🔋 Consider switching to renewable energy sources or improving energy efficiency.")
    if waste > 500:
        recs.append("♻️ Implement waste reduction and recycling programs.")
    if water > 2000:
        recs.append("💧 Adopt water-saving technologies and practices.")
    if not recs:
        recs.append("✅ Excellent! Your operations are highly sustainable.")
    return recs

# -------------------- Display ESG Score and Recommendations --------------------
if submitted:
    score = calculate_esg_score(energy_consumption, waste_generated, water_usage)

    st.markdown("## 🧾 Your ESG Score")
    if score >= 80:
        color = "green"
        status = "Excellent"
    elif score >= 60:
        color = "orange"
        status = "Good"
    else:
        color = "red"
        status = "Needs Improvement"

    st.markdown(f"""
    <div style='border:2px solid {color}; border-radius:10px; padding:20px; text-align:center; background-color:#f9f9f9;'>
        <h2 style='color:{color};'>{score:.2f} / 100</h2>
        <h4>Status: <span style='color:{color};'>{status}</span></h4>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("## 🛠️ Tailored Recommendations")
    for rec in get_recommendations(energy_consumption, waste_generated, water_usage):
        st.success(rec)

# -------------------- Green Finance Opportunities --------------------
st.markdown("---")
st.subheader("💰 Explore Green Finance Opportunities")

try:
    df = pd.read_csv("data/green_finance_db.csv")
    df["Website"] = df["Website"].apply(lambda x: f"[Visit]({x})")
    st.dataframe(df, use_container_width=True)
except FileNotFoundError:
    st.warning("Green finance database not found. Please upload `data/green_finance_db.csv`.")

