import streamlit as st

st.set_page_config(page_title="GreenInvest Analytics", page_icon="🌱")

st.title("🌿 GreenInvest Analytics - ESG Scoring for SMEs")

with st.form("esg_form"):
    st.header("Input Your ESG Data")

    energy_consumption = st.number_input("Energy Consumption (kWh/month)", min_value=0.0)
    waste_generated = st.number_input("Waste Generated (kg/month)", min_value=0.0)
    water_usage = st.number_input("Water Usage (liters/month)", min_value=0.0)

    submitted = st.form_submit_button("Calculate ESG Score")

def calculate_esg_score(energy, waste, water):
    score = 100 - (energy * 0.3 + waste * 0.4 + water * 0.3)
    return max(min(score, 100), 0)

def get_recommendations(energy, waste, water):
    recs = []
    if energy > 1000:
        recs.append("Consider switching to renewable energy sources or improving energy efficiency.")
    if waste > 500:
        recs.append("Implement waste reduction and recycling programs.")
    if water > 2000:
        recs.append("Adopt water-saving technologies and practices.")
    if not recs:
        recs.append("Great job! Keep maintaining sustainable operations.")
    return recs

if submitted:
    score = calculate_esg_score(energy_consumption, waste_generated, water_usage)
    st.metric("Your ESG Score", f"{score:.2f} / 100")

    st.subheader("Recommendations")
    recs = get_recommendations(energy_consumption, waste_generated, water_usage)
    for rec in recs:
        st.write("- " + rec)
