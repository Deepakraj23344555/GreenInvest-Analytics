import streamlit as st
import pandas as pd

# -------------------- Page Setup --------------------
st.set_page_config(page_title="GreenInvest Analytics", page_icon="🌱", layout="wide")

# -------------------- Sidebar --------------------
with st.sidebar:
    st.title("📊 About GreenInvest")
    st.markdown("""
    GreenInvest Analytics empowers **SMEs** to measure and improve their **ESG performance**.

    🌿 Input operational data  
    🌿 Receive an ESG score  
    🌿 Get personalized sustainability tips  
    🌿 Access green finance based on your score  
    """)
    st.markdown("---")
    st.markdown("📧 Contact: greeninvest@example.com")

# -------------------- Title --------------------
st.markdown("<h1 style='text-align: center;'>🌱 GreenInvest Analytics</h1>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align: center; color: grey;'>Empowering SMEs to Measure, Improve, and Fund Sustainability</h5>", unsafe_allow_html=True)
st.markdown("---")

# -------------------- Form --------------------
st.subheader("📥 ESG Metrics Input")

with st.form("esg_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        energy = st.number_input("🔌 Energy Consumption (kWh/month)", min_value=0.0)
    with col2:
        waste = st.number_input("🗑️ Waste Generated (kg/month)", min_value=0.0)
    with col3:
        water = st.number_input("🚰 Water Usage (liters/month)", min_value=0.0)
    submitted = st.form_submit_button("📊 Calculate ESG Score")

# -------------------- Logic Functions --------------------
def calculate_esg_score(energy, waste, water):
    score = 100 - (energy * 0.03 + waste * 0.04 + water * 0.02)
    return max(min(score, 100), 0)

def get_score_status(score):
    if score >= 80:
        return "Excellent", "green"
    elif score >= 60:
        return "Good", "orange"
    else:
        return "Needs Improvement", "red"

def get_score_recommendations(score):
    if score >= 80:
        return [
            "✅ Your ESG performance is excellent. Maintain current standards.",
            "📈 You may qualify for ESG-focused investment capital.",
            "🌟 Consider publishing a sustainability report to improve transparency."
        ]
    elif score >= 60:
        return [
            "♻️ Improve waste segregation or use recyclable materials.",
            "💧 Install water-saving devices or optimize usage.",
            "🔋 Explore partial transition to renewable energy."
        ]
    else:
        return [
            "🆘 High carbon footprint: Begin with energy audits.",
            "🔄 Start a basic waste and water management program.",
            "📚 Attend ESG training or consult local sustainability advisors."
        ]

def filter_finance_opportunities(df, score):
    if score < 60:
        return df[df["Type"] == "Grant"]
    elif score < 80:
        return df[df["Type"] == "Loan"]
    else:
        return df[df["Type"] == "Investor"]

# -------------------- Result Display --------------------
if submitted:
    score = calculate_esg_score(energy, waste, water)
    status, color = get_score_status(score)

    st.markdown("## 🧾 Your ESG Score")
    st.markdown(f"""
    <div style='border:2px solid {color}; border-radius:10px; padding:20px; text-align:center; background-color:#f9f9f9;'>
        <h2 style='color:{color};'>{score:.2f} / 100</h2>
        <h4>Status: <span style='color:{color};'>{status}</span></h4>
    </div>
    """, unsafe_allow_html=True)

    # Recommendations
    st.markdown("## 🛠️ Tailored Sustainability Recommendations")
    for rec in get_score_recommendations(score):
        st.success(rec)

    # Finance Opportunities
    st.markdown("---")
    st.markdown("## 💰 Finance Opportunities Based on Your ESG Score")

    try:
        df = pd.read_csv("data/green_finance_db.csv")
        df["Website"] = df["Website"].apply(lambda x: f"[Visit]({x})")
        filtered = filter_finance_opportunities(df, score)

        if not filtered.empty:
            st.dataframe(filtered.reset_index(drop=True), use_container_width=True)
        else:
            st.info("No finance opportunities matched your score. Check back later!")

    except FileNotFoundError:
        st.warning("⚠️ Missing file: `data/green_finance_db.csv` not found.")

import plotly.express as px

# Store and update ESG history (temporary, not persistent)
if "score_history" not in st.session_state:
    st.session_state.score_history = []

if submitted:
    st.session_state.score_history.append(score)

# Show ESG trend
if len(st.session_state.score_history) > 1:
    st.markdown("## 📊 ESG Score Trend")
    trend_df = pd.DataFrame({
        "Attempt": list(range(1, len(st.session_state.score_history) + 1)),
        "ESG Score": st.session_state.score_history
    })
    fig = px.line(trend_df, x="Attempt", y="ESG Score", markers=True)
    st.plotly_chart(fig, use_container_width=True)

