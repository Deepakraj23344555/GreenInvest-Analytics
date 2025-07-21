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

# --- ESG Score Calculation Logic ---
# This is a simplified model. In a real-world scenario, this would be much more complex,
# involving industry benchmarks, normalization, and more sophisticated weighting.
def calculate_esg_score(env_data, social_data, gov_data):
    # Weights for each category (must sum to 1)
    weights = {'E': 0.4, 'S': 0.3, 'G': 0.3}

    # --- Environmental Score (example logic) ---
    # Lower is better for consumption/waste, higher is better for recycling.
    # We'll normalize them to a 0-100 scale.
    energy_score = max(0, 100 - (env_data['energy'] / 1000)) # Penalize high energy use
    water_score = max(0, 100 - (env_data['water'] / 500))    # Penalize high water use
    waste_score = max(0, 100 - (env_data['waste'] / 100))     # Penalize high waste generation
    recycling_score = env_data['recycling'] # Already a percentage
    
    e_score = (energy_score + water_score + waste_score + recycling_score) / 4

    # --- Social Score (example logic) ---
    # Lower is better for turnover/incidents, higher is better for diversity/training.
    turnover_score = max(0, 100 - (social_data['turnover'] * 2)) # Penalize high turnover
    safety_score = max(0, 100 - (social_data['incidents'] * 10)) # Penalize incidents
    diversity_score = social_data['diversity']
    
    s_score = (turnover_score + safety_score + diversity_score) / 3

    # --- Governance Score (example logic) ---
    # Higher is better for both.
    independence_score = gov_data['independence']
    ethics_score = gov_data['ethics']

    g_score = (independence_score + ethics_score) / 2

    # --- Final Weighted ESG Score ---
    final_score = (e_score * weights['E']) + (s_score * weights['S']) + (g_score * weights['G'])
    
    return final_score, e_score, s_score, g_score

# --- UI ---
st.title("🌿 GreenInvest Analytics")
st.markdown("Welcome to the GreenInvest Analytics platform. Our goal is to help SMEs measure, improve, and report on their ESG performance to unlock green finance opportunities.")

st.info("This is a demonstration platform. Please enter your company's data in the sidebar on the left and click 'Calculate ESG Score' to see your results.", icon="ℹ️")

# --- Sidebar for Data Input ---
st.sidebar.header("Step 1: Input Your Data")
st.sidebar.markdown("Provide the following metrics for the last reporting year.")

# --- Environmental Inputs ---
with st.sidebar.expander("🌳 Environmental", expanded=True):
    energy_consumption = st.number_input("Annual Energy Consumption (kWh)", min_value=0, value=50000)
    water_usage = st.number_input("Annual Water Usage (cubic meters)", min_value=0, value=2500)
    waste_generation = st.number_input("Annual Waste Generated (kg)", min_value=0, value=1000)
    recycling_rate = st.slider("Recycling Rate (%)", min_value=0, max_value=100, value=40)
    env_data = {
        'energy': energy_consumption, 
        'water': water_usage, 
        'waste': waste_generation, 
        'recycling': recycling_rate
    }

# --- Social Inputs ---
with st.sidebar.expander("❤️ Social", expanded=True):
    employee_turnover = st.slider("Employee Turnover Rate (%)", min_value=0, max_value=100, value=15)
    safety_incidents = st.number_input("Number of Safety Incidents", min_value=0, value=3)
    diversity_ratio = st.slider("Management Diversity (e.g., % women in leadership)", min_value=0, max_value=100, value=30)
    social_data = {
        'turnover': employee_turnover,
        'incidents': safety_incidents,
        'diversity': diversity_ratio
    }

# --- Governance Inputs ---
with st.sidebar.expander("⚖️ Governance", expanded=True):
    board_independence = st.slider("Board Independence (%)", min_value=0, max_value=100, value=50)
    ethics_training = st.slider("Ethics Training Completion (%)", min_value=0, max_value=100, value=85)
    gov_data = {
        'independence': board_independence,
        'ethics': ethics_training
    }

# --- Calculation Button ---
if st.sidebar.button("Calculate ESG Score", type="primary", use_container_width=True):
    # --- Calculation ---
    final_score, e_score, s_score, g_score = calculate_esg_score(env_data, social_data, gov_data)

    # --- Dashboard Display ---
    st.header("Your ESG Performance Dashboard")
    
    # Top-level score
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric(label="Overall ESG Score", value=f"{final_score:.1f}", delta="out of 100")
        st.write("This score reflects your overall performance across Environmental, Social, and Governance factors.")

    with col2:
        # Gauge Chart
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = final_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "ESG Score"},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#2E8B57"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': '#FFB6C1'},
                    {'range': [50, 80], 'color': '#FFFFE0'},
                    {'range': [80, 100], 'color': '#98FB98'}],
            }))
        fig.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Detailed score breakdown
    st.subheader("Score Breakdown")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="🌳 Environmental Score", value=f"{e_score:.1f}")
    with col2:
        st.metric(label="❤️ Social Score", value=f"{s_score:.1f}")
    with col3:
        st.metric(label="⚖️ Governance Score", value=f"{g_score:.1f}")

else:
    st.header("Your ESG Dashboard")
    st.write("Your results will be displayed here once you input your data and calculate the score.")


# --- Footer ---
st.markdown("---")
st.write("Made with ❤️ for a greener future.")

