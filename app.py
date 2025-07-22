pip install SQLAlchemy
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

# -------------------- PAGE CONFIG --------------------
# Set the page configuration for the Streamlit app
st.set_page_config(page_title="GreenInvest Analytics Dashboard", layout="wide")

# Custom CSS for animations and styling
st.markdown("""
    <style>
        /* Fade-in-up animation for the welcome banner */
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .welcome-banner {
            animation: fadeInUp 1s ease-out;
        }
        /* Animated gradient background for the main app */
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
        /* Sidebar styling */
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

# Welcome banner at the top of the page
st.markdown("""
    <div class="welcome-banner" style="text-align:center; padding: 2rem 1rem;
            border-radius: 15px; background: linear-gradient(to right, #89f7fe, #66a6ff);
            color: #ffffff; font-size: 2.5rem; font-weight: bold;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            box-shadow: 0 0 20px rgba(0,0,0,0.3);">
        🚀 Welcome to the <span style="color: #ffdf00;">✨ GreenInvest Analytics</span>!
    </div>
""", unsafe_allow_html=True)

# Create 'feedback' table if it doesn't exist
from sqlalchemy import create_engine

feedback_engine = create_engine('sqlite:///feedback.db')

with feedback_engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS feedback (
            username TEXT,
            message TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    conn.commit()

# -------------------- AUTH HELPERS --------------------
def hash_password(password):
    """Hashes a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    """Verifies user credentials against the database."""
    df = pd.read_sql("SELECT * FROM users WHERE username = ?", user_engine, params=(username,))
    return not df.empty and df['password'][0] == hash_password(password)

def register_user(username, password):
    """Registers a new user if the username doesn't already exist."""
    df = pd.read_sql("SELECT * FROM users WHERE username = ?", user_engine, params=(username,))
    if not df.empty:
        return False
    with user_engine.connect() as conn:
        conn.execute(
            text("INSERT INTO users (username, password) VALUES (:u, :p)"),
            {"u": username, "p": hash_password(password)}
        )
        conn.commit()
    return True

def save_feedback(username, message):
    """Saves user feedback to the database."""
    with feedback_engine.connect() as conn:
        conn.execute(
            text("INSERT INTO feedback (username, message) VALUES (:u, :m)"),
            {"u": username, "m": message}
        )
        conn.commit()

# --- MOCK DATABASE & HELPER FUNCTIONS (No changes here) ---
FINANCE_OPPORTUNITIES = [
    {"name": "GreenStart Grant Program", "type": "Grant", "description": "A grant for businesses starting their sustainability journey. Covers up to 50% of the cost for an initial energy audit.", "minimum_esg_score": 0, "icon": "🌱", "url": "https://www.sba.gov/funding-programs/grants"},
    {"name": "Eco-Efficiency Business Loan", "type": "Loan", "description": "Low-interest loans for SMEs investing in energy-efficient equipment or renewable energy installations.", "minimum_esg_score": 60, "icon": "💡", "url": "https://www.bankofamerica.com/smallbusiness/business-financing/"},
    {"name": "Sustainable Supply Chain Fund", "type": "Venture Capital", "description": "Equity investment for companies demonstrating strong ESG performance and a commitment to a sustainable supply chain.", "minimum_esg_score": 75, "icon": "🤝", "url": "https://www.blackrock.com/corporate/sustainability"},
    {"name": "Circular Economy Innovators Fund", "type": "Venture Capital", "description": "Seed funding for businesses pioneering models in waste reduction, recycling, and resource circularity.", "minimum_esg_score": 80, "icon": "♻️", "url": "https://www.closedlooppartners.com/"},
    {"name": "Impact Investors Alliance - Premier Partner", "type": "Private Equity", "description": "For top-tier ESG performers. Provides significant growth capital and access to a global network of sustainable businesses.", "minimum_esg_score": 90, "icon": "🏆", "url": "https://thegiin.org/"}
]

def calculate_esg_score(env_data, social_data, gov_data):
    weights = {'E': 0.4, 'S': 0.3, 'G': 0.3}
    e_score = (max(0, 100 - (env_data['energy'] / 1000)) + max(0, 100 - (env_data['water'] / 500)) + max(0, 100 - (env_data['waste'] / 100)) + env_data['recycling']) / 4
    s_score = (max(0, 100 - (social_data['turnover'] * 2)) + max(0, 100 - (social_data['incidents'] * 10)) + social_data['diversity']) / 3
    g_score = (gov_data['independence'] + gov_data['ethics']) / 2
    final_score = (e_score * weights['E']) + (s_score * weights['S']) + (g_score * weights['G'])
    return final_score, e_score, s_score, g_score

def get_recommendations(e_score, s_score, g_score):
    recs = {'E': [], 'S': [], 'G': []}
    if e_score < 70: recs['E'].append("**High Impact:** Conduct a professional energy audit.")
    if e_score < 80: recs['E'].append("**Medium Impact:** Implement a company-wide switch to LED lighting.")
    if s_score < 70: recs['S'].append("**High Impact:** Introduce an anonymous employee feedback system to understand turnover.")
    if g_score < 75: recs['G'].append("**High Impact:** Appoint an additional independent director to your board.")
    if not recs['E']: recs['E'].append("Strong performance! Continue monitoring and explore new green technologies.")
    if not recs['S']: recs['S'].append("Excellent metrics! Focus on maintaining this positive culture.")
    if not recs['G']: recs['G'].append("Solid governance. Stay updated with best practices.")
    return recs

def get_financial_opportunities(esg_score):
    return [opp for opp in FINANCE_OPPORTUNITIES if esg_score >= opp['minimum_esg_score']]

# --- Function to display the full dashboard ---
def display_dashboard(final_score, e_score, s_score, g_score):
    st.header("Your ESG Performance Dashboard")
    overall_score_placeholder = st.empty()
    time.sleep(0.5)
    for i in range(int(final_score) + 1):
        overall_score_placeholder.metric(label="Overall ESG Score", value=f"{i:.1f}", delta="out of 100")
        time.sleep(0.02)
    overall_score_placeholder.metric(label="Overall ESG Score", value=f"{final_score:.1f}", delta="out of 100")

    tab1, tab2, tab3 = st.tabs(["📊 Dashboard Breakdown", "🎯 Recommendations", "💰 Finance Marketplace"])
    with tab1:
        # ... (charting code remains the same)
        st.subheader("Performance Overview")
        col1, col2 = st.columns(2)
        with col1:
            fig_spider = go.Figure()
            fig_spider.add_trace(go.Scatterpolar(r=[e_score, s_score, g_score, e_score], theta=['Environmental', 'Social', 'Governance', 'Environmental'], fill='toself', name='Your Score', line_color='green'))
            fig_spider.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, title="ESG Balanced Scorecard", height=350)
            st.plotly_chart(fig_spider, use_container_width=True)
        with col2:
            fig_bar = go.Figure(go.Bar(x=[e_score, s_score, g_score], y=['Environmental', 'Social', 'Governance'], orientation='h', marker_color=['#2E8B57', '#6B8E23', '#8FBC8F']))
            fig_bar.update_layout(title="Score Breakdown", xaxis_title="Score (out of 100)", height=350)
            st.plotly_chart(fig_bar, use_container_width=True)
        if final_score > 85:
            st.balloons()
            st.success("Congratulations! Your high ESG score is outstanding and unlocks premium opportunities.")
    with tab2:
        # ... (recommendations code remains the same)
        st.header("Actionable Recommendations")
        recommendations = get_recommendations(e_score, s_score, g_score)
        with st.container(border=True):
            st.subheader("🌳 Environmental")
            for rec in recommendations['E']: st.markdown(f"- {rec}")
        with st.container(border=True):
            st.subheader("❤️ Social")
            for rec in recommendations['S']: st.markdown(f"- {rec}")
        with st.container(border=True):
            st.subheader("⚖️ Governance")
            for rec in recommendations['G']: st.markdown(f"- {rec}")
    with tab3:
        # ... (marketplace code remains the same)
        st.header("Your Green Finance Marketplace")
        st.write(f"Based on your ESG score of **{final_score:.1f}**, you have unlocked the following opportunities.")
        unlocked_opportunities = get_financial_opportunities(final_score)
        if not unlocked_opportunities:
            st.warning("Improve your ESG score to unlock your first financial opportunities.")
        else:
            for opp in unlocked_opportunities:
                with st.container(border=True):
                    st.subheader(f"{opp['icon']} {opp['name']}")
                    st.write(f"**Type:** {opp['type']} | **Minimum ESG Score:** {opp['minimum_esg_score']}")
                    st.write(opp['description'])
                    st.link_button("Apply Now", opp['url'])

# --- UI ---
st.title("🌿 GreenInvest Analytics")
st.markdown("An interactive tool for SMEs to measure, improve, and report on their ESG performance to unlock green finance opportunities.")

# --- Sidebar ---
st.sidebar.header("Step 1: Choose Input Method")
input_method = st.sidebar.radio("Select how you want to provide data:", ("Manual Input", "Upload CSV File"))

# --- Create a sample CSV for download ---
@st.cache_data
def get_template_csv():
    template_data = {
        'metric': [
            'energy_consumption_kwh', 'water_usage_m3', 'waste_generation_kg', 'recycling_rate_pct',
            'employee_turnover_pct', 'safety_incidents_count', 'management_diversity_pct',
            'board_independence_pct', 'ethics_training_pct'
        ],
        'value': [50000, 2500, 1000, 40, 15, 3, 30, 50, 85]
    }
    df = pd.DataFrame(template_data)
    return df.to_csv(index=False).encode('utf-8')

# --- Display input fields based on user's choice ---
if input_method == "Manual Input":
    st.sidebar.header("Step 2: Input Your Data")
    with st.sidebar.expander("🌳 Environmental", expanded=True):
        energy_consumption = st.number_input("Annual Energy Consumption (kWh)", min_value=0, value=50000)
        water_usage = st.number_input("Annual Water Usage (cubic meters)", min_value=0, value=2500)
        waste_generation = st.number_input("Annual Waste Generated (kg)", min_value=0, value=1000)
        recycling_rate = st.slider("Recycling Rate (%)", min_value=0, max_value=100, value=40)
    with st.sidebar.expander("❤️ Social", expanded=True):
        employee_turnover = st.slider("Employee Turnover Rate (%)", min_value=0, max_value=100, value=15)
        safety_incidents = st.number_input("Number of Safety Incidents", min_value=0, value=3)
        diversity_ratio = st.slider("Management Diversity (%)", min_value=0, max_value=100, value=30)
    with st.sidebar.expander("⚖️ Governance", expanded=True):
        board_independence = st.slider("Board Independence (%)", min_value=0, max_value=100, value=50)
        ethics_training = st.slider("Ethics Training Completion (%)", min_value=0, max_value=100, value=85)
    
    if st.sidebar.button("Calculate ESG Score", type="primary", use_container_width=True):
        env_data = {'energy': energy_consumption, 'water': water_usage, 'waste': waste_generation, 'recycling': recycling_rate}
        social_data = {'turnover': employee_turnover, 'incidents': safety_incidents, 'diversity': diversity_ratio}
        gov_data = {'independence': board_independence, 'ethics': ethics_training}
        final_score, e_score, s_score, g_score = calculate_esg_score(env_data, social_data, gov_data)
        display_dashboard(final_score, e_score, s_score, g_score)
    else:
        st.info("Enter your data manually in the sidebar and click 'Calculate ESG Score'.")

else: # CSV Upload
    st.sidebar.header("Step 2: Upload Your Data")
    uploaded_file = st.sidebar.file_uploader("Upload your ESG data file (.csv)", type=["csv"])
    
    st.sidebar.download_button(
        label="Download Template CSV",
        data=get_template_csv(),
        file_name="esg_data_template.csv",
        mime="text/csv",
        use_container_width=True
    )

    if uploaded_file is not None:
        try:
            data_df = pd.read_csv(uploaded_file)
            # Convert the two-column format to a dictionary
            data_dict = pd.Series(data_df.value.values, index=data_df.metric).to_dict()

            # Extract data
            env_data = {
                'energy': data_dict['energy_consumption_kwh'],
                'water': data_dict['water_usage_m3'],
                'waste': data_dict['waste_generation_kg'],
                'recycling': data_dict['recycling_rate_pct']
            }
            social_data = {
                'turnover': data_dict['employee_turnover_pct'],
                'incidents': data_dict['safety_incidents_count'],
                'diversity': data_dict['management_diversity_pct']
            }
            gov_data = {
                'independence': data_dict['board_independence_pct'],
                'ethics': data_dict['ethics_training_pct']
            }
            
            st.sidebar.success("File uploaded and processed successfully!")
            
            # Calculate and display
            final_score, e_score, s_score, g_score = calculate_esg_score(env_data, social_data, gov_data)
            display_dashboard(final_score, e_score, s_score, g_score)

        except Exception as e:
            st.error(f"An error occurred processing the file: {e}")
            st.warning("Please make sure your CSV file follows the format of the template.")
    else:
        st.info("Upload a CSV file using the sidebar to see your ESG analysis.")


st.markdown("---")
st.write("Made with ❤️ for a greener future.")
