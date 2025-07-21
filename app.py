import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(
    page_title="GreenInvest Analytics",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MOCK DATABASE of Financial Opportunities ---
# In a real app, this would come from a database.
FINANCE_OPPORTUNITIES = [
    {
        "name": "GreenStart Grant Program",
        "type": "Grant",
        "description": "A grant for businesses starting their sustainability journey. Covers up to 50% of the cost for an initial energy audit.",
        "minimum_esg_score": 0, # Available to everyone
        "icon": "🌱"
    },
    {
        "name": "Eco-Efficiency Business Loan",
        "type": "Loan",
        "description": "Low-interest loans for SMEs investing in energy-efficient equipment or renewable energy installations.",
        "minimum_esg_score": 60,
        "icon": "💡"
    },
    {
        "name": "Sustainable Supply Chain Fund",
        "type": "Venture Capital",
        "description": "Equity investment for companies demonstrating strong ESG performance and a commitment to a sustainable supply chain.",
        "minimum_esg_score": 75,
        "icon": "🤝"
    },
    {
        "name": "Circular Economy Innovators Fund",
        "type": "Venture Capital",
        "description": "Seed funding for businesses pioneering models in waste reduction, recycling, and resource circularity.",
        "minimum_esg_score": 80,
        "icon": "♻️"
    },
    {
        "name": "Impact Investors Alliance - Premier Partner",
        "type": "Private Equity",
        "description": "For top-tier ESG performers. Provides significant growth capital and access to a global network of sustainable businesses.",
        "minimum_esg_score": 90,
        "icon": "🏆"
    }
]


# --- ESG Score Calculation Logic ---
def calculate_esg_score(env_data, social_data, gov_data):
    weights = {'E': 0.4, 'S': 0.3, 'G': 0.3}
    e_score = (max(0, 100 - (env_data['energy'] / 1000)) + max(0, 100 - (env_data['water'] / 500)) + max(0, 100 - (env_data['waste'] / 100)) + env_data['recycling']) / 4
    s_score = (max(0, 100 - (social_data['turnover'] * 2)) + max(0, 100 - (social_data['incidents'] * 10)) + social_data['diversity']) / 3
    g_score = (gov_data['independence'] + gov_data['ethics']) / 2
    final_score = (e_score * weights['E']) + (s_score * weights['S']) + (g_score * weights['G'])
    return final_score, e_score, s_score, g_score

# --- Recommendations Engine Logic ---
def get_recommendations(e_score, s_score, g_score):
    recs = {'E': [], 'S': [], 'G': []}
    if e_score < 70: recs['E'].append("**High Impact:** Conduct a professional energy audit.")
    if e_score < 80: recs['E'].append("**Medium Impact:** Implement a company-wide switch to LED lighting.")
    if e_score < 60: recs['E'].append("**High Impact:** Invest in smart meters for real-time utility tracking.")
    if e_score < 90 and not recs['E']: recs['E'].append("**Low Hanging Fruit:** Improve waste segregation and recycling campaign.")
    if s_score < 70: recs['S'].append("**High Impact:** Introduce an anonymous employee feedback system to understand turnover.")
    if s_score < 80: recs['S'].append("**Medium Impact:** Formalize a mentorship program.")
    if s_score < 60: recs['S'].append("**High Impact:** Review and enhance safety protocols and training frequency.")
    if g_score < 75: recs['G'].append("**High Impact:** Appoint an additional independent director to your board.")
    if g_score < 85: recs['G'].append("**Medium Impact:** Publish a formal code of conduct and business ethics.")
    if not recs['E']: recs['E'].append("Strong performance! Continue monitoring and explore new green technologies.")
    if not recs['S']: recs['S'].append("Excellent metrics! Focus on maintaining this positive culture.")
    if not recs['G']: recs['G'].append("Solid governance. Stay updated with best practices.")
    return recs

# --- NEW: Financial Opportunities Logic ---
def get_financial_opportunities(esg_score):
    return [opp for opp in FINANCE_OPPORTUNITIES if esg_score >= opp['minimum_esg_score']]

# --- UI ---
st.title("🌿 GreenInvest Analytics")
st.markdown("An interactive tool for SMEs to measure, improve, and report on their ESG performance to unlock green finance opportunities.")

st.info("Enter your company's data in the sidebar and click 'Calculate ESG Score' to see your results.", icon="ℹ️")

# --- Sidebar for Data Input ---
st.sidebar.header("Step 1: Input Your Data")
st.sidebar.markdown("Provide metrics for the last reporting year.")

with st.sidebar.expander("🌳 Environmental", expanded=True):
    energy_consumption = st.number_input("Annual Energy Consumption (kWh)", min_value=0, value=50000)
    water_usage = st.number_input("Annual Water Usage (cubic meters)", min_value=0, value=2500)
    waste_generation = st.number_input("Annual Waste Generated (kg)", min_value=0, value=1000)
    recycling_rate = st.slider("Recycling Rate (%)", min_value=0, max_value=100, value=40)
    env_data = {'energy': energy_consumption, 'water': water_usage, 'waste': waste_generation, 'recycling': recycling_rate}

with st.sidebar.expander("❤️ Social", expanded=True):
    employee_turnover = st.slider("Employee Turnover Rate (%)", min_value=0, max_value=100, value=15)
    safety_incidents = st.number_input("Number of Safety Incidents", min_value=0, value=3)
    diversity_ratio = st.slider("Management Diversity (%)", min_value=0, max_value=100, value=30)
    social_data = {'turnover': employee_turnover, 'incidents': safety_incidents, 'diversity': diversity_ratio}

with st.sidebar.expander("⚖️ Governance", expanded=True):
    board_independence = st.slider("Board Independence (%)", min_value=0, max_value=100, value=50)
    ethics_training = st.slider("Ethics Training Completion (%)", min_value=0, max_value=100, value=85)
    gov_data = {'independence': board_independence, 'ethics': ethics_training}

if st.sidebar.button("Calculate ESG Score", type="primary", use_container_width=True):
    final_score, e_score, s_score, g_score = calculate_esg_score(env_data, social_data, gov_data)

    st.header("Your ESG Performance Dashboard")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric(label="Overall ESG Score", value=f"{final_score:.1f}", delta="out of 100")
        st.write("This score reflects your overall performance across Environmental, Social, and Governance factors.")

    with col2:
        fig = go.Figure(go.Indicator(
            mode = "gauge+number", value = final_score,
            domain = {'x': [0, 1], 'y': [0, 1]}, title = {'text': "ESG Score"},
            gauge = {
                'axis': {'range': [None, 100]}, 'bar': {'color': "#2E8B57"},
                'steps': [
                    {'range': [0, 50], 'color': '#FFB6C1'}, {'range': [50, 80], 'color': '#FFFFE0'}, {'range': [80, 100], 'color': '#98FB98'}],
            }))
        fig.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("Score Breakdown")
    col1, col2, col3 = st.columns(3)
    st.metric("🌳 Environmental Score", f"{e_score:.1f}", delta_color="off", label_visibility="visible")
    st.metric("❤️ Social Score", f"{s_score:.1f}", delta_color="off", label_visibility="visible")
    st.metric("⚖️ Governance Score", f"{g_score:.1f}", delta_color="off", label_visibility="visible")

    st.markdown("---")
    st.header("Actionable Recommendations")
    recommendations = get_recommendations(e_score, s_score, g_score)
    with st.expander("🌳 Environmental Recommendations"):
        for rec in recommendations['E']: st.markdown(f"- {rec}")
    with st.expander("❤️ Social Recommendations"):
        for rec in recommendations['S']: st.markdown(f"- {rec}")
    with st.expander("⚖️ Governance Recommendations"):
        for rec in recommendations['G']: st.markdown(f"- {rec}")

    # --- NEW: Display Financial Opportunities ---
    st.markdown("---")
    st.header("Your Green Finance Marketplace")
    st.write(f"Based on your ESG score of **{final_score:.1f}**, you have unlocked the following opportunities. Improve your score to unlock more!")
    
    unlocked_opportunities = get_financial_opportunities(final_score)

    if not unlocked_opportunities:
        st.warning("Improve your ESG score to unlock your first financial opportunities.")
    else:
        for opp in unlocked_opportunities:
            st.subheader(f"{opp['icon']} {opp['name']}")
            st.write(f"**Type:** {opp['type']}")
            st.write(opp['description'])
            st.button("Apply Now (Example)", key=opp['name'])
            st.markdown("---")

else:
    st.header("Your ESG Dashboard")
    st.write("Your results will be displayed here once you input your data and calculate the score.")

st.markdown("---")
st.write("Made with ❤️ for a greener future.")
