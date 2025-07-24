import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import json
import sqlite3
import datetime

# Import Authenticate and Hasher from streamlit_authenticator
from streamlit_authenticator import Authenticate, Hasher

# --- Page Configuration ---
st.set_page_config(
    page_title="GreenInvest Analytics",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
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

        /* Main App Background */
        .stApp {
            background: linear-gradient(to right, #f0fff0, #e6f5d0, #e0f7fa);
            animation: gradient 15s ease infinite;
            background-size: 400% 400%;
            color: #1b3a2f;
        }

        @keyframes gradient {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }

        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background: linear-gradient(to bottom, #2e7d32, #388e3c);
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stTabs [data-baseweb="tab"],
        section[data-testid="stSidebar"] .stTextInput label {
            color: #ffffff !important;
        }
        section[data-testid="stSidebar"] .stTabs [aria-selected="true"] {
            font-weight: bold;
            border-bottom: 2px solid #dcedc8;
        }
    </style>
""", unsafe_allow_html=True)


# --- DATABASE SETUP ---
DATABASE_NAME = 'esg_data.db'

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS esg_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            overall_score REAL,
            e_score REAL,
            s_score REAL,
            g_score REAL,
            env_data TEXT,
            social_data TEXT,
            gov_data TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def add_user(username, password_hash, name):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash, name) VALUES (?, ?, ?)",
                  (username, password_hash, name))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_id(username):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_id = c.fetchone()
    conn.close()
    return user_id[0] if user_id else None

def save_esg_history(user_id, timestamp, overall, e, s, g, env_data, social_data, gov_data):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO esg_history (user_id, timestamp, overall_score, e_score, s_score, g_score, env_data, social_data, gov_data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (user_id, timestamp, overall, e, s, g, json.dumps(env_data), json.dumps(social_data), json.dumps(gov_data)))
    conn.commit()
    conn.close()

def get_esg_history(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT timestamp, overall_score, e_score, s_score, g_score, env_data, social_data, gov_data FROM esg_history WHERE user_id = ? ORDER BY timestamp ASC", (user_id,))
    history_data = c.fetchall()
    conn.close()
    parsed_history = []
    for row in history_data:
        parsed_history.append({
            'timestamp': pd.to_datetime(row[0]),
            'overall_score': row[1], 'e_score': row[2], 's_score': row[3], 'g_score': row[4],
            'env_data': json.loads(row[5]) if row[5] else {},
            'social_data': json.loads(row[6]) if row[6] else {},
            'gov_data': json.loads(row[7]) if row[7] else {},
        })
    return parsed_history

init_db()


# --- CORE LOGIC & HELPER FUNCTIONS ---
FINANCE_OPPORTUNITIES = [
    {"name": "GreenStart Grant Program", "type": "Grant", "description": "A grant for businesses starting their sustainability journey. Covers up to 50% of the cost for an initial energy audit.", "minimum_esg_score": 0, "icon": "🌱", "url": "https://www.sba.gov/funding-programs/grants"},
    {"name": "Eco-Efficiency Business Loan", "type": "Loan", "description": "Low-interest loans for SMEs investing in energy-efficient equipment or renewable energy installations.", "minimum_esg_score": 60, "icon": "💡", "url": "https://www.bankofamerica.com/smallbusiness/business-financing/"},
    {"name": "Sustainable Supply Chain Fund", "type": "Venture Capital", "description": "Equity investment for companies demonstrating strong ESG performance and a commitment to a sustainable supply chain.", "minimum_esg_score": 75, "icon": "🤝", "url": "https://www.blackrock.com/corporate/sustainability"},
    {"name": "Circular Economy Innovators Fund", "type": "Venture Capital", "description": "Seed funding for businesses pioneering models in waste reduction, recycling, and resource circularity.", "minimum_esg_score": 80, "icon": "♻️", "url": "https://www.closedlooppartners.com/"},
    {"name": "Impact Investors Alliance - Premier Partner", "type": "Private Equity", "description": "For top-tier ESG performers. Provides significant growth capital and access to a global network of sustainable businesses.", "minimum_esg_score": 90, "icon": "🏆", "url": "https://thegiin.org/"}
]
INDUSTRY_AVERAGES = {'Environmental': 70, 'Social': 65, 'Governance': 75, 'Overall ESG': 70}
CO2_EMISSION_FACTORS = {'energy_kwh_to_co2': 0.4, 'water_m3_to_co2': 0.1, 'waste_kg_to_co2': 0.5}
DEFAULT_INPUT_DATA = {
    'env': {'energy': 50000, 'water': 2500, 'waste': 1000, 'recycling': 40},
    'social': {'turnover': 15, 'incidents': 3, 'diversity': 30},
    'gov': {'independence': 50, 'ethics': 85}
}

def calculate_esg_score(env_data, social_data, gov_data):
    weights = {'E': 0.4, 'S': 0.3, 'G': 0.3}
    e_score = (max(0, 100 - (env_data['energy'] / 1000)) + max(0, 100 - (env_data['water'] / 500)) + max(0, 100 - (env_data['waste'] / 100)) + env_data['recycling']) / 4
    s_score = (max(0, 100 - (social_data['turnover'] * 2)) + max(0, 100 - (social_data['incidents'] * 10)) + social_data['diversity']) / 3
    g_score = (gov_data['independence'] + gov_data['ethics']) / 2
    final_score = (e_score * weights['E']) + (s_score * weights['S']) + (g_score * weights['G'])
    return final_score, e_score, s_score, g_score

def get_recommendations(e_score, s_score, g_score):
    recs = {'E': [], 'S': [], 'G': []}
    if e_score < 70: recs['E'].append("**High Impact:** Conduct a professional energy audit to identify efficiency opportunities.")
    if e_score < 80: recs['E'].append("**Medium Impact:** Implement a company-wide switch to LED lighting and optimize HVAC systems.")
    if e_score < 60: recs['E'].append("**Critical:** Develop a comprehensive waste reduction and recycling strategy.")

    if s_score < 70: recs['S'].append("**High Impact:** Introduce an anonymous employee feedback system to understand turnover causes.")
    if s_score < 80: recs['S'].append("**Medium Impact:** Implement diversity and inclusion training for all employees and management.")
    if s_score < 60: recs['S'].append("**Critical:** Review safety protocols and conduct mandatory safety training sessions to reduce incidents.")

    if g_score < 75: recs['G'].append("**High Impact:** Appoint an additional independent director to your board for objective oversight.")
    if g_score < 85: recs['G'].append("**Medium Impact:** Regularly update and communicate your company's ethics policy and training.")
    if g_score < 65: recs['G'].append("**Critical:** Establish a clear whistleblower policy and ensure board accountability mechanisms are in place.")

    if not recs['E']: recs['E'].append("Strong performance! Continue monitoring and explore new green technologies to stay ahead.")
    if not recs['S']: recs['S'].append("Excellent metrics! Focus on maintaining this positive culture and fostering employee well-being.")
    if not recs['G']: recs['G'].append("Solid governance. Stay updated with best practices and ensure robust internal controls.")
    return recs

def get_financial_opportunities(esg_score):
    return [opp for opp in FINANCE_OPPORTUNITIES if esg_score >= opp['minimum_esg_score']]

def calculate_environmental_impact(env_data):
    energy_co2 = env_data.get('energy', 0) * CO2_EMISSION_FACTORS['energy_kwh_to_co2']
    water_co2 = env_data.get('water', 0) * CO2_EMISSION_FACTORS['water_m3_to_co2']
    waste_co2 = env_data.get('waste', 0) * CO2_EMISSION_FACTORS['waste_kg_to_co2']
    total_co2 = energy_co2 + water_co2 + waste_co2
    return {'total_co2_kg': total_co2, 'energy_co2_kg': energy_co2, 'water_co2_kg': water_co2, 'waste_co2_kg': waste_co2}


# --- UI DISPLAY FUNCTIONS ---
def display_dashboard(final_score, e_score, s_score, g_score, env_data, social_data, gov_data, current_user_id):
    st.header(f"Your ESG Performance Dashboard, {st.session_state.name}!")

    # Animated Overall Score
    overall_score_placeholder = st.empty()
    time.sleep(0.5)
    for i in range(int(final_score) + 1):
        overall_score_placeholder.metric(label="Overall ESG Score", value=f"{i:.1f}", delta="out of 100")
        time.sleep(0.02)
    overall_score_placeholder.metric(label="Overall ESG Score", value=f"{final_score:.1f}", delta="out of 100")

    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Performance Overview", "🎯 Recommendations", "💰 Finance Marketplace", "🕰️ Historical Trends", "🧪 Scenario Planner"])

    with tab1:
        st.subheader("Performance Breakdown & Environmental Impact")
        col_e, col_s, col_g = st.columns(3)
        col_e.metric("🌳 Environmental", f"{e_score:.1f}")
        col_s.metric("❤️ Social", f"{s_score:.1f}")
        col_g.metric("⚖️ Governance", f"{g_score:.1f}")
        st.divider()

        impact_data = calculate_environmental_impact(env_data)
        st.subheader("🌍 Environmental Impact Estimation")
        st.info(f"Based on your environmental data, your estimated annual **CO2 equivalent emissions are {impact_data['total_co2_kg']:.2f} kg**.")
        st.markdown(f"- **Energy:** {impact_data['energy_co2_kg']:.2f} kg CO₂e\n- **Water:** {impact_data['water_co2_kg']:.2f} kg CO₂e\n- **Waste:** {impact_data['waste_co2_kg']:.2f} kg CO₂e")
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            fig_spider = go.Figure()
            fig_spider.add_trace(go.Scatterpolar(r=[e_score, s_score, g_score, e_score], theta=['Environmental', 'Social', 'Governance', 'Environmental'], fill='toself', name='Your Score', line_color=st.get_option('theme.primaryColor')))
            fig_spider.add_trace(go.Scatterpolar(r=[INDUSTRY_AVERAGES['Environmental'], INDUSTRY_AVERAGES['Social'], INDUSTRY_AVERAGES['Governance'], INDUSTRY_AVERAGES['Environmental']], theta=['Environmental', 'Social', 'Governance', 'Environmental'], fill='none', name='Industry Average', line_color='grey', line_dash='dot'))
            fig_spider.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, title="ESG Balanced Scorecard", height=350, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_spider, use_container_width=True)
        with col2:
            fig_bar = go.Figure(go.Bar(x=[e_score, s_score, g_score], y=['Environmental', 'Social', 'Governance'], orientation='h', marker_color=['#4CAF50', '#8BC34A', '#CDDC39']))
            fig_bar.update_layout(title="Score Breakdown", xaxis_title="Score (out of 100)", height=350)
            st.plotly_chart(fig_bar, use_container_width=True)

        if final_score > 85:
            st.balloons()
            # --- CHANGE --- Hardcoded name "KD" replaced with dynamic session state name.
            st.success(f"Congratulations, {st.session_state.name}! Your high ESG score is outstanding and unlocks premium opportunities.")

    with tab2:
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
                    st.link_button(f"Learn More & Apply {opp['icon']}", opp['url'])

    with tab4:
        st.header("🕰️ Your ESG Performance History")
        history = get_esg_history(current_user_id)
        if not history:
            st.info("No historical data found. Calculate your score to start tracking your progress.")
        else:
            history_df = pd.DataFrame(history)
            fig_history_overall = go.Figure(go.Scatter(x=history_df['timestamp'], y=history_df['overall_score'], mode='lines+markers', name='Overall Score', line_color=st.get_option('theme.primaryColor')))
            fig_history_overall.update_layout(title="Overall ESG Score Over Time", xaxis_title="Date", yaxis_title="Score (0-100)")
            st.plotly_chart(fig_history_overall, use_container_width=True)

            fig_history_esg = go.Figure()
            fig_history_esg.add_trace(go.Scatter(x=history_df['timestamp'], y=history_df['e_score'], mode='lines+markers', name='Environmental', line_color='#4CAF50'))
            fig_history_esg.add_trace(go.Scatter(x=history_df['timestamp'], y=history_df['s_score'], mode='lines+markers', name='Social', line_color='#8BC34A'))
            fig_history_esg.add_trace(go.Scatter(x=history_df['timestamp'], y=history_df['g_score'], mode='lines+markers', name='Governance', line_color='#CDDC39'))
            fig_history_esg.update_layout(title="ESG Category Scores Over Time", xaxis_title="Date", yaxis_title="Score (0-100)")
            st.plotly_chart(fig_history_esg, use_container_width=True)

            st.subheader("Raw Historical Data")
            st.dataframe(history_df[['timestamp', 'overall_score', 'e_score', 's_score', 'g_score']].set_index('timestamp').sort_index(ascending=False))

    with tab5:
        st.header("🧪 Scenario Planner: What If...?")
        st.write("Adjust the metrics below to see how your ESG score and opportunities would change.")
        
        # --- CHANGE --- Simplified logic to get current data for the planner.
        current_data = st.session_state.get('current_esg_input_data', DEFAULT_INPUT_DATA)
        
        st.subheader("Adjust Metrics for Scenario")
        col_s1, col_s2, col_s3 = st.columns(3)

        with col_s1:
            st.markdown("##### 🌳 Environmental")
            scenario_energy = st.number_input("Energy Consumption (kWh)", value=current_data['env']['energy'], key='scenario_energy')
            scenario_water = st.number_input("Water Usage (m³)", value=current_data['env']['water'], key='scenario_water')
            scenario_waste = st.number_input("Waste Generated (kg)", value=current_data['env']['waste'], key='scenario_waste')
            scenario_recycling = st.slider("Recycling Rate (%)", 0, 100, value=current_data['env']['recycling'], key='scenario_recycling')
        with col_s2:
            st.markdown("##### ❤️ Social")
            scenario_turnover = st.slider("Employee Turnover Rate (%)", 0, 100, value=current_data['social']['turnover'], key='scenario_turnover')
            scenario_incidents = st.number_input("Safety Incidents", min_value=0, value=current_data['social']['incidents'], key='scenario_incidents')
            scenario_diversity = st.slider("Management Diversity (%)", 0, 100, value=current_data['social']['diversity'], key='scenario_diversity')
        with col_s3:
            st.markdown("##### ⚖️ Governance")
            scenario_independence = st.slider("Board Independence (%)", 0, 100, value=current_data['gov']['independence'], key='scenario_independence')
            scenario_ethics = st.slider("Ethics Training Completion (%)", 0, 100, value=current_data['gov']['ethics'], key='scenario_ethics')

        scenario_env_data = {'energy': scenario_energy, 'water': scenario_water, 'waste': scenario_waste, 'recycling': scenario_recycling}
        scenario_social_data = {'turnover': scenario_turnover, 'incidents': scenario_incidents, 'diversity': scenario_diversity}
        scenario_gov_data = {'independence': scenario_independence, 'ethics': scenario_ethics}
        
        scenario_final_score, scenario_e_score, scenario_s_score, scenario_g_score = calculate_esg_score(scenario_env_data, scenario_social_data, scenario_gov_data)

        st.subheader("Projected Scenario Results")
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.metric("Projected Overall ESG Score", f"{scenario_final_score:.1f}", f"{scenario_final_score - final_score:.1f}")
            st.metric("Projected Environmental Score", f"{scenario_e_score:.1f}", f"{scenario_e_score - e_score:.1f}")
            st.metric("Projected Social Score", f"{scenario_s_score:.1f}", f"{scenario_s_score - s_score:.1f}")
            st.metric("Projected Governance Score", f"{scenario_g_score:.1f}", f"{scenario_g_score - g_score:.1f}")
        with col_res2:
            st.markdown("##### Projected Unlocked Opportunities")
            scenario_unlocked_opportunities = get_financial_opportunities(scenario_final_score)
            if not scenario_unlocked_opportunities:
                st.warning("No opportunities unlocked in this scenario.")
            else:
                for opp in scenario_unlocked_opportunities:
                    st.markdown(f"- {opp['icon']} {opp['name']} (Min ESG: {opp['minimum_esg_score']})")
    
    st.divider()
    report_data = {
        "User": st.session_state.username, "Report_Date": datetime.datetime.now().isoformat(),
        "Overall_ESG_Score": f"{final_score:.1f}", "Environmental_Score": f"{e_score:.1f}", "Social_Score": f"{s_score:.1f}", "Governance_Score": f"{g_score:.1f}",
        "Input_Data": {"Environmental": env_data, "Social": social_data, "Governance": gov_data},
        "Environmental_Impact_Estimation": calculate_environmental_impact(env_data),
        "Recommendations": get_recommendations(e_score, s_score, g_score),
        "Unlocked_Financial_Opportunities": [{"name": opp['name'], "type": opp['type'], "min_esg": opp['minimum_esg_score']} for opp in unlocked_opportunities],
        "Industry_Benchmark_Averages": INDUSTRY_AVERAGES
    }
    st.download_button(label="📥 Download Full ESG Report (JSON)", data=json.dumps(report_data, indent=4), file_name=f"ESG_Report_{st.session_state.username}_{datetime.date.today()}.json", mime="application/json", use_container_width=True)

# --- CHANGE --- Registration form refactored into its own function to avoid duplication.
def display_registration_form(form_key_suffix):
    with st.expander("New User? Register Here", expanded=True):
        st.subheader("Register for GreenInvest Analytics")
        with st.form(f"register_form_{form_key_suffix}"):
            new_name = st.text_input("Your Name", key=f"reg_name_{form_key_suffix}")
            new_username = st.text_input("New Username", key=f"reg_username_{form_key_suffix}")
            new_password = st.text_input("New Password", type="password", key=f"reg_password_{form_key_suffix}")
            confirm_password = st.text_input("Confirm Password", type="password", key=f"reg_confirm_password_{form_key_suffix}")
            
            if st.form_submit_button("Register"):
                if not all([new_name, new_username, new_password, confirm_password]):
                    st.error("Please fill out all fields.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(new_username) < 3 or len(new_password) < 6:
                    st.error("Username must be at least 3 characters and password at least 6 characters.")
                else:
                    hashed_password = Hasher([new_password]).generate()[0]
                    if add_user(new_username, hashed_password, new_name):
                        st.success("You have successfully registered! Please log in above.")
                        st.balloons()
                    else:
                        st.error("Username already exists. Please choose a different one.")

# --- CHANGE --- Logic to process data and display the dashboard is now in its own function.
def process_and_display_data(env_data, social_data, gov_data):
    """Calculates scores, saves to DB, stores in session, and displays the dashboard."""
    final_score, e_score, s_score, g_score = calculate_esg_score(env_data, social_data, gov_data)
    
    # Save current input data to session state for scenario planner and pre-filling
    current_input = {'env': env_data, 'social': social_data, 'gov': gov_data}
    st.session_state.current_esg_input_data = current_input
    
    # Save to database
    save_esg_history(st.session_state.user_id, datetime.datetime.now().isoformat(),
                     final_score, e_score, s_score, g_score,
                     env_data, social_data, gov_data)
    
    # Display the full dashboard
    display_dashboard(final_score, e_score, s_score, g_score, env_data, social_data, gov_data, st.session_state.user_id)


# --- AUTHENTICATION & MAIN APP LOGIC ---

# Get user credentials from the database
def get_all_users_for_authenticator():
    conn = sqlite3.connect(DATABASE_NAME)
    users_data = conn.execute("SELECT name, username, password_hash FROM users").fetchall()
    conn.close()
    credentials = {"usernames": {}}
    for name, username, password_hash in users_data:
        credentials["usernames"][username] = {"name": name, "password": password_hash}
    return credentials

credentials = get_all_users_for_authenticator()

authenticator = Authenticate(
    credentials,
    'greeninvest_cookie',
    'this_should_be_a_very_strong_secret_key', # IMPORTANT: Change this!
    cookie_expiry_days=30
)

# Render the welcome banner on every run
st.markdown("""
    <div class="welcome-banner" style="text-align:center; padding: 2rem 1rem;
         border-radius: 15px; background: linear-gradient(to right, #a5d6a7, #81d4fa);
         color: #003300; font-size: 2.5rem; font-weight: bold;
         font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
         box-shadow: 0 0 15px rgba(0,0,0,0.2);">
        🌿 Welcome to <span style="color: #1b5e20;">GreenInvest Analytics</span> — Powering Sustainable Wealth 🌱
    </div>
""", unsafe_allow_html=True)
st.write(" ") # Add some space

# Main logic starts here
name, authentication_status, username = authenticator.login(form_name='Login', location='main')

if st.session_state["authentication_status"]:
    # --- User is authenticated ---
    st.session_state.username = username
    st.session_state.name = name
    st.session_state.user_id = get_user_id(username)
    
    # --- CHANGE --- Use the correct keyword argument for the logout button.
    authenticator.logout(button_name='Logout', location='sidebar', key='logout_button')
    
    st.sidebar.title(f"Welcome, {st.session_state.name}!")
    st.sidebar.divider()

    # --- Sidebar for Data Input ---
    st.sidebar.header("Step 1: Provide Your Data")
    input_method = st.sidebar.radio("Input Method:", ("Manual Input", "Upload CSV File"), label_visibility="collapsed")
    
    # --- CHANGE --- Unified session state for input data, pre-filled from history or defaults.
    if 'current_esg_input_data' not in st.session_state:
        user_history = get_esg_history(st.session_state.user_id)
        if user_history:
            latest_entry = user_history[-1]
            st.session_state.current_esg_input_data = {
                'env': latest_entry['env_data'],
                'social': latest_entry['social_data'],
                'gov': latest_entry['gov_data']
            }
        else:
            st.session_state.current_esg_input_data = DEFAULT_INPUT_DATA
    
    current_inputs = st.session_state.current_esg_input_data

    # Manual Input Form
    if input_method == "Manual Input":
        with st.sidebar.form(key='manual_input_form'):
            with st.expander("🌳 Environmental", expanded=True):
                energy = st.number_input("Annual Energy (kWh)", value=current_inputs['env']['energy'])
                water = st.number_input("Annual Water (m³)", value=current_inputs['env']['water'])
                waste = st.number_input("Annual Waste (kg)", value=current_inputs['env']['waste'])
                recycling = st.slider("Recycling Rate (%)", 0, 100, value=current_inputs['env']['recycling'])
            with st.expander("❤️ Social", expanded=True):
                turnover = st.slider("Employee Turnover (%)", 0, 100, value=current_inputs['social']['turnover'])
                incidents = st.number_input("Safety Incidents", min_value=0, value=current_inputs['social']['incidents'])
                diversity = st.slider("Management Diversity (%)", 0, 100, value=current_inputs['social']['diversity'])
            with st.expander("⚖️ Governance", expanded=True):
                independence = st.slider("Board Independence (%)", 0, 100, value=current_inputs['gov']['independence'])
                ethics = st.slider("Ethics Training (%)", 0, 100, value=current_inputs['gov']['ethics'])
            
            submitted = st.form_submit_button("Calculate ESG Score", type="primary", use_container_width=True)
            if submitted:
                env_data = {'energy': energy, 'water': water, 'waste': waste, 'recycling': recycling}
                social_data = {'turnover': turnover, 'incidents': incidents, 'diversity': diversity}
                gov_data = {'independence': independence, 'ethics': ethics}
                # --- CHANGE --- Call the refactored processing function
                process_and_display_data(env_data, social_data, gov_data)

    # CSV Upload
    else:
        st.sidebar.header("Upload Data File")
        uploaded_file = st.sidebar.file_uploader("Upload a CSV file following the template format.", type=["csv"])
        
        @st.cache_data
        def get_template_csv():
            df = pd.DataFrame({'metric': list(DEFAULT_INPUT_DATA['env'].keys()) + list(DEFAULT_INPUT_DATA['social'].keys()) + list(DEFAULT_INPUT_DATA['gov'].keys()), 'value': [50000, 2500, 1000, 40, 15, 3, 30, 50, 85]})
            return df.to_csv(index=False).encode('utf-8')

        st.sidebar.download_button(label="Download Template CSV", data=get_template_csv(), file_name="esg_data_template.csv", mime="text/csv", use_container_width=True)

        if uploaded_file:
            try:
                data_df = pd.read_csv(uploaded_file).set_index('metric')['value'].to_dict()
                env_data = {'energy': data_df['energy'], 'water': data_df['water'], 'waste': data_df['waste'], 'recycling': data_df['recycling']}
                social_data = {'turnover': data_df['turnover'], 'incidents': data_df['incidents'], 'diversity': data_df['diversity']}
                gov_data = {'independence': data_df['independence'], 'ethics': data_df['ethics']}
                st.sidebar.success("File processed successfully!")
                # --- CHANGE --- Call the refactored processing function
                process_and_display_data(env_data, social_data, gov_data)
            except Exception as e:
                st.sidebar.error(f"Error processing file: {e}. Please ensure it matches the template.")

    # --- CHANGE --- On initial login, if no button has been clicked yet, show the last known dashboard.
    if 'submitted' not in locals() and not uploaded_file:
        user_history = get_esg_history(st.session_state.user_id)
        if user_history:
            st.info("Displaying your most recent ESG report. Use the sidebar to analyze new data.")
            latest_entry = user_history[-1]
            display_dashboard(latest_entry['overall_score'], latest_entry['e_score'], latest_entry['s_score'], latest_entry['g_score'], latest_entry['env_data'], latest_entry['social_data'], latest_entry['gov_data'], st.session_state.user_id)
        else:
            st.info("👋 Welcome! Please provide your company's data in the sidebar to calculate your first ESG score.")

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect.')
    display_registration_form("error_case") # Use the refactored function

elif st.session_state["authentication_status"] is None:
    st.info('Please log in or register to access the GreenInvest Analytics platform.')
    display_registration_form("initial_case") # Use the refactored function

# Footer
st.divider()
st.markdown("<p style='text-align: center; color: grey;'>Made with ❤️ for a greener future. – GreenInvest Analytics</p>", unsafe_allow_html=True)
