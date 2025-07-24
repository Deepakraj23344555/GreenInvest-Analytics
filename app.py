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
    page_title="Ecolytics",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- NEW --- Define the username for the admin user
ADMIN_USERNAME = "admin"

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
    """Initializes the database and creates tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT
        )
    ''')
    # ESG history table
    c.execute('''
        CREATE TABLE IF NOT EXISTS esg_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            overall_score REAL, e_score REAL, s_score REAL, g_score REAL,
            env_data TEXT, social_data TEXT, gov_data TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    # --- NEW --- Login history table to track user logins
    c.execute('''
        CREATE TABLE IF NOT EXISTS login_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            login_timestamp TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def add_user(username, password_hash, name):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash, name) VALUES (?, ?, ?)", (username, password_hash, name))
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

# --- NEW --- Function to save a login event to the database
def save_login_record(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO login_history (user_id, login_timestamp) VALUES (?, ?)",
              (user_id, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

# --- NEW --- Functions to get data for the admin panel
def get_all_registered_users():
    conn = sqlite3.connect(DATABASE_NAME)
    df = pd.read_sql_query("SELECT id, username, name FROM users", conn)
    conn.close()
    return df

def get_full_login_history():
    conn = sqlite3.connect(DATABASE_NAME)
    query = """
    SELECT
        u.username,
        u.name,
        lh.login_timestamp
    FROM login_history lh
    JOIN users u ON lh.user_id = u.id
    ORDER BY lh.login_timestamp DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    df['login_timestamp'] = pd.to_datetime(df['login_timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    return df

# Initialize the database on first run
init_db()


# --- CORE LOGIC & HELPER FUNCTIONS ---
FINANCE_OPPORTUNITIES = [
    {"name": "GreenStart Grant Program", "type": "Grant", "description": "A grant for businesses starting their sustainability journey.", "minimum_esg_score": 0, "icon": "🌱", "url": "https://www.sba.gov/funding-programs/grants"},
    {"name": "Eco-Efficiency Business Loan", "type": "Loan", "description": "Low-interest loans for SMEs investing in energy-efficient equipment.", "minimum_esg_score": 60, "icon": "💡", "url": "https://www.bankofamerica.com/smallbusiness/business-financing/"},
    {"name": "Sustainable Supply Chain Fund", "type": "Venture Capital", "description": "Equity investment for companies with strong ESG performance.", "minimum_esg_score": 75, "icon": "🤝", "url": "https://www.blackrock.com/corporate/sustainability"},
    {"name": "Circular Economy Innovators Fund", "type": "Venture Capital", "description": "Seed funding for businesses pioneering models in circularity.", "minimum_esg_score": 80, "icon": "♻️", "url": "https://www.closedlooppartners.com/"},
    {"name": "Impact Investors Alliance - Premier Partner", "type": "Private Equity", "description": "For top-tier ESG performers. Provides significant growth capital.", "minimum_esg_score": 90, "icon": "🏆", "url": "https://thegiin.org/"}
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
    e_score = (max(0, 100 - (env_data.get('energy', 0) / 1000)) + max(0, 100 - (env_data.get('water', 0) / 500)) + max(0, 100 - (env_data.get('waste', 0) / 100)) + env_data.get('recycling', 0)) / 4
    s_score = (max(0, 100 - (social_data.get('turnover', 0) * 2)) + max(0, 100 - (social_data.get('incidents', 0) * 10)) + social_data.get('diversity', 0)) / 3
    g_score = (gov_data.get('independence', 0) + gov_data.get('ethics', 0)) / 2
    final_score = (e_score * weights['E']) + (s_score * weights['S']) + (g_score * weights['G'])
    return final_score, e_score, s_score, g_score

def get_recommendations(e_score, s_score, g_score):
    recs = {'E': [], 'S': [], 'G': []}
    if e_score < 70: recs['E'].append("**High Impact:** Conduct a professional energy audit.")
    if e_score < 80: recs['E'].append("**Medium Impact:** Switch to LED lighting and optimize HVAC systems.")
    if e_score < 60: recs['E'].append("**Critical:** Develop a comprehensive waste reduction strategy.")
    if s_score < 70: recs['S'].append("**High Impact:** Introduce an anonymous employee feedback system.")
    if s_score < 80: recs['S'].append("**Medium Impact:** Implement diversity and inclusion training.")
    if s_score < 60: recs['S'].append("**Critical:** Review and enhance safety protocols.")
    if g_score < 75: recs['G'].append("**High Impact:** Appoint an additional independent director.")
    if g_score < 85: recs['G'].append("**Medium Impact:** Regularly update and communicate your ethics policy.")
    if g_score < 65: recs['G'].append("**Critical:** Establish a clear whistleblower policy.")
    if not recs['E']: recs['E'].append("Strong performance! Continue monitoring and explore new green tech.")
    if not recs['S']: recs['S'].append("Excellent metrics! Focus on maintaining a positive culture.")
    if not recs['G']: recs['G'].append("Solid governance. Stay updated with best practices.")
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
    overall_score_placeholder = st.empty()
    for i in range(int(final_score) + 1):
        overall_score_placeholder.metric(label="Overall ESG Score", value=f"{i:.1f}", delta="out of 100")
        time.sleep(0.01)
    overall_score_placeholder.metric(label="Overall ESG Score", value=f"{final_score:.1f}", delta="out of 100")
    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Performance", "🎯 Recommendations", "💰 Finance", "🕰️ History", "🧪 Scenarios"])

    with tab1:
        st.subheader("Performance Breakdown & Environmental Impact")
        col_e, col_s, col_g = st.columns(3)
        col_e.metric("🌳 Environmental", f"{e_score:.1f}")
        col_s.metric("❤️ Social", f"{s_score:.1f}")
        col_g.metric("⚖️ Governance", f"{g_score:.1f}")
        st.divider()
        impact_data = calculate_environmental_impact(env_data)
        st.subheader("🌍 Environmental Impact Estimation")
        st.info(f"Estimated annual **CO2 equivalent emissions: {impact_data['total_co2_kg']:.2f} kg**.")
        st.markdown(f"- **Energy:** {impact_data['energy_co2_kg']:.2f} kg CO₂e\n- **Water:** {impact_data['water_co2_kg']:.2f} kg CO₂e\n- **Waste:** {impact_data['waste_co2_kg']:.2f} kg CO₂e")
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            fig_spider = go.Figure()
            fig_spider.add_trace(go.Scatterpolar(r=[e_score, s_score, g_score, e_score], theta=['E', 'S', 'G', 'E'], fill='toself', name='Your Score'))
            fig_spider.add_trace(go.Scatterpolar(r=[INDUSTRY_AVERAGES['Environmental'], INDUSTRY_AVERAGES['Social'], INDUSTRY_AVERAGES['Governance'], INDUSTRY_AVERAGES['Environmental']], theta=['E', 'S', 'G', 'E'], fill='none', name='Industry Avg', line_dash='dot'))
            fig_spider.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, title="ESG Balanced Scorecard", height=350)
            st.plotly_chart(fig_spider, use_container_width=True)
        with col2:
            fig_bar = go.Figure(go.Bar(x=[e_score, s_score, g_score], y=['Environmental', 'Social', 'Governance'], orientation='h', marker_color=['#4CAF50', '#8BC34A', '#CDDC39']))
            fig_bar.update_layout(title="Score Breakdown", xaxis_title="Score (out of 100)", height=350)
            st.plotly_chart(fig_bar, use_container_width=True)
        if final_score > 85:
            st.balloons()
            st.success(f"Congratulations, {st.session_state.name}! Your high ESG score is outstanding.")

    with tab2:
        st.header("Actionable Recommendations")
        recs = get_recommendations(e_score, s_score, g_score)
        for cat, cat_recs in recs.items():
            st.subheader(f"{'🌳' if cat == 'E' else '❤️' if cat == 'S' else '⚖️'} {cat}")
            for rec in cat_recs: st.markdown(f"- {rec}")

    with tab3:
        st.header("Your Green Finance Marketplace")
        st.write(f"Based on your ESG score of **{final_score:.1f}**, you qualify for:")
        unlocked = get_financial_opportunities(final_score)
        if not unlocked: st.warning("Improve your ESG score to unlock financial opportunities.")
        else:
            for opp in unlocked:
                with st.container(border=True):
                    st.subheader(f"{opp['icon']} {opp['name']}")
                    st.write(f"**Type:** {opp['type']} | **Min. Score:** {opp['minimum_esg_score']}")
                    st.write(opp['description'])
                    st.link_button(f"Learn More {opp['icon']}", opp['url'])

    with tab4:
        st.header("🕰️ Your ESG Performance History")
        history = get_esg_history(current_user_id)
        if not history: st.info("No history found. Calculate a score to start tracking.")
        else:
            hist_df = pd.DataFrame(history)
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Scatter(x=hist_df['timestamp'], y=hist_df['overall_score'], name='Overall', mode='lines+markers'))
            fig_hist.add_trace(go.Scatter(x=hist_df['timestamp'], y=hist_df['e_score'], name='Environmental', mode='lines+markers'))
            fig_hist.add_trace(go.Scatter(x=hist_df['timestamp'], y=hist_df['s_score'], name='Social', mode='lines+markers'))
            fig_hist.add_trace(go.Scatter(x=hist_df['timestamp'], y=hist_df['g_score'], name='Governance', mode='lines+markers'))
            fig_hist.update_layout(title="ESG Score Over Time", xaxis_title="Date", yaxis_title="Score")
            st.plotly_chart(fig_hist, use_container_width=True)
            st.dataframe(hist_df[['timestamp', 'overall_score', 'e_score', 's_score', 'g_score']].set_index('timestamp'))

    with tab5:
        st.header("🧪 Scenario Planner")
        st.write("Adjust metrics to see how your score could change.")
        current_data = st.session_state.get('current_esg_input_data', DEFAULT_INPUT_DATA)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("##### 🌳 Environmental")
            s_energy = st.number_input("Energy (kWh)", value=current_data['env']['energy'])
            s_water = st.number_input("Water (m³)", value=current_data['env']['water'])
            s_waste = st.number_input("Waste (kg)", value=current_data['env']['waste'])
            s_recycling = st.slider("Recycling (%)", 0, 100, current_data['env']['recycling'])
        with col2:
            st.markdown("##### ❤️ Social")
            s_turnover = st.slider("Turnover (%)", 0, 100, current_data['social']['turnover'])
            s_incidents = st.number_input("Incidents", min_value=0, value=current_data['social']['incidents'])
            s_diversity = st.slider("Diversity (%)", 0, 100, current_data['social']['diversity'])
        with col3:
            st.markdown("##### ⚖️ Governance")
            s_independence = st.slider("Independence (%)", 0, 100, current_data['gov']['independence'])
            s_ethics = st.slider("Ethics Training (%)", 0, 100, current_data['gov']['ethics'])

        s_env = {'energy': s_energy, 'water': s_water, 'waste': s_waste, 'recycling': s_recycling}
        s_soc = {'turnover': s_turnover, 'incidents': s_incidents, 'diversity': s_diversity}
        s_gov = {'independence': s_independence, 'ethics': s_ethics}
        s_final, s_e, s_s, s_g = calculate_esg_score(s_env, s_soc, s_gov)

        st.subheader("Projected Results")
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.metric("Projected Overall ESG Score", f"{s_final:.1f}", f"{s_final - final_score:.1f}")
            st.metric("Projected Environmental Score", f"{s_e:.1f}", f"{s_e - e_score:.1f}")
            st.metric("Projected Social Score", f"{s_s:.1f}", f"{s_s - s_score:.1f}")
            st.metric("Projected Governance Score", f"{s_g:.1f}", f"{s_g - g_score:.1f}")
        with col_res2:
            st.markdown("##### Projected Unlocked Opportunities")
            s_unlocked = get_financial_opportunities(s_final)
            if not s_unlocked: st.warning("No opportunities unlocked.")
            else:
                for opp in s_unlocked: st.markdown(f"- {opp['icon']} {opp['name']}")

def display_registration_form(form_key_suffix):
    with st.expander("New User? Register Here", expanded=True):
        st.subheader("Register for Ecolytics")
        with st.form(f"register_form_{form_key_suffix}"):
            new_name = st.text_input("Your Name", key=f"reg_name_{form_key_suffix}")
            new_username = st.text_input("New Username", key=f"reg_username_{form_key_suffix}")
            new_password = st.text_input("New Password", type="password", key=f"reg_password_{form_key_suffix}")
            if st.form_submit_button("Register"):
                if not all([new_name, new_username, new_password]):
                    st.error("Please fill out all fields.")
                elif len(new_username) < 3 or len(new_password) < 6:
                    st.error("Username must be at least 3 characters and password at least 6.")
                else:
                    hashed_password = Hasher([new_password]).generate()[0]
                    if add_user(new_username, hashed_password, new_name):
                        st.success("Registration successful! Please log in above.")
                        st.balloons()
                    else:
                        st.error("Username already exists.")

def process_and_display_data(env_data, social_data, gov_data):
    final_score, e_score, s_score, g_score = calculate_esg_score(env_data, social_data, gov_data)
    st.session_state.current_esg_input_data = {'env': env_data, 'social': social_data, 'gov': gov_data}
    save_esg_history(st.session_state.user_id, datetime.datetime.now().isoformat(), final_score, e_score, s_score, g_score, env_data, social_data, gov_data)
    display_dashboard(final_score, e_score, s_score, g_score, env_data, social_data, gov_data, st.session_state.user_id)

# --- NEW --- Admin Panel Display Function
def display_admin_panel():
    with st.sidebar.expander("👑 Admin Panel", expanded=False):
        st.subheader("Registered Users")
        st.dataframe(get_all_registered_users(), use_container_width=True)
        st.subheader("User Login History")
        st.dataframe(get_full_login_history(), use_container_width=True)


# --- AUTHENTICATION & MAIN APP LOGIC ---
def get_all_users_for_authenticator():
    conn = sqlite3.connect(DATABASE_NAME)
    users_data = conn.execute("SELECT name, username, password_hash FROM users").fetchall()
    conn.close()
    credentials = {"usernames": {}}
    for name, username, password_hash in users_data:
        credentials["usernames"][username] = {"name": name, "password": password_hash}
    return credentials

# Welcome Banner
st.markdown("""
    <div class="welcome-banner" style="text-align:center; padding: 2rem 1rem; border-radius: 15px; background: linear-gradient(to right, #a5d6a7, #81d4fa); color: #003300; font-size: 2.5rem; font-weight: bold; font-family: 'Segoe UI', sans-serif; box-shadow: 0 0 15px rgba(0,0,0,0.2);">
        🌿 Welcome to <span style="color: #1b5e20;">Ecolytics</span>
    </div>
""", unsafe_allow_html=True)
st.write(" ")

credentials = get_all_users_for_authenticator()
authenticator = Authenticate(credentials, 'ecolytics_cookie', 'a_strong_secret_key', cookie_expiry_days=30)
name, authentication_status, username = authenticator.login(form_name='Login', location='main')

if st.session_state["authentication_status"]:
    # --- User is authenticated ---
    st.session_state.username = username
    st.session_state.name = name
    st.session_state.user_id = get_user_id(username)

    if 'login_recorded' not in st.session_state:
        save_login_record(st.session_state.user_id)
        st.session_state.login_recorded = True

    authenticator.logout(button_name='Logout', location='sidebar', key='logout_button')
    st.sidebar.title(f"Welcome, {st.session_state.name}!")
    st.sidebar.divider()

    st.sidebar.header("Step 1: Provide Your Data")
    input_method = st.sidebar.radio("Input Method:", ("Manual Input", "Upload CSV"), label_visibility="collapsed")
    
    if 'current_esg_input_data' not in st.session_state:
        user_history = get_esg_history(st.session_state.user_id)
        st.session_state.current_esg_input_data = user_history[-1] if user_history else DEFAULT_INPUT_DATA

    current_inputs = st.session_state.current_esg_input_data

    if input_method == "Manual Input":
        with st.sidebar.form(key='manual_input_form'):
            with st.expander("🌳 Environmental", expanded=True):
                energy = st.number_input("Annual Energy (kWh)", value=current_inputs['env'].get('energy', 0))
                water = st.number_input("Annual Water (m³)", value=current_inputs['env'].get('water', 0))
                waste = st.number_input("Annual Waste (kg)", value=current_inputs['env'].get('waste', 0))
                recycling = st.slider("Recycling Rate (%)", 0, 100, value=current_inputs['env'].get('recycling', 0))
            with st.expander("❤️ Social", expanded=True):
                turnover = st.slider("Employee Turnover (%)", 0, 100, value=current_inputs['social'].get('turnover', 0))
                incidents = st.number_input("Safety Incidents", min_value=0, value=current_inputs['social'].get('incidents', 0))
                diversity = st.slider("Management Diversity (%)", 0, 100, value=current_inputs['social'].get('diversity', 0))
            with st.expander("⚖️ Governance", expanded=True):
                independence = st.slider("Board Independence (%)", 0, 100, value=current_inputs['gov'].get('independence', 0))
                ethics = st.slider("Ethics Training (%)", 0, 100, value=current_inputs['gov'].get('ethics', 0))
            
            if st.form_submit_button("Calculate ESG Score", type="primary", use_container_width=True):
                env_data = {'energy': energy, 'water': water, 'waste': waste, 'recycling': recycling}
                social_data = {'turnover': turnover, 'incidents': incidents, 'diversity': diversity}
                gov_data = {'independence': independence, 'ethics': ethics}
                process_and_display_data(env_data, social_data, gov_data)

    else: # CSV Upload
        st.sidebar.header("Upload Data File")
        uploaded_file = st.sidebar.file_uploader("Upload a CSV file.", type=["csv"])
        
        @st.cache_data
        def get_template_csv():
            df = pd.DataFrame({'metric': list(DEFAULT_INPUT_DATA['env'].keys()) + list(DEFAULT_INPUT_DATA['social'].keys()) + list(DEFAULT_INPUT_DATA['gov'].keys()), 'value': [v for d in DEFAULT_INPUT_DATA.values() for v in d.values()]})
            return df.to_csv(index=False).encode('utf-8')

        st.sidebar.download_button(label="Download Template CSV", data=get_template_csv(), file_name="esg_template.csv", mime="text/csv", use_container_width=True)

        if uploaded_file:
            try:
                data_df = pd.read_csv(uploaded_file).set_index('metric')['value'].to_dict()
                env_data = {k: data_df.get(k, 0) for k in DEFAULT_INPUT_DATA['env']}
                social_data = {k: data_df.get(k, 0) for k in DEFAULT_INPUT_DATA['social']}
                gov_data = {k: data_df.get(k, 0) for k in DEFAULT_INPUT_DATA['gov']}
                st.sidebar.success("File processed successfully!")
                process_and_display_data(env_data, social_data, gov_data)
            except Exception as e:
                st.sidebar.error(f"Error processing file: {e}")

    # --- Main content display logic ---
    if not (input_method == "Manual Input" and 'env_data' in locals()) and not uploaded_file:
        user_history = get_esg_history(st.session_state.user_id)
        if user_history:
            st.info("Displaying your most recent ESG report. Use the sidebar to analyze new data.")
            latest_entry = user_history[-1]
            display_dashboard(latest_entry['overall_score'], latest_entry['e_score'], latest_entry['s_score'], latest_entry['g_score'], latest_entry['env_data'], latest_entry['social_data'], latest_entry['gov_data'], st.session_state.user_id)
        else:
            st.info("👋 Welcome! Please provide your company's data in the sidebar to calculate your first ESG score.")

    # --- NEW --- Display Admin Panel for the admin user
    if st.session_state.username == ADMIN_USERNAME:
        display_admin_panel()

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect.')
    display_registration_form("error_case")

elif st.session_state["authentication_status"] is None:
    st.info('Please log in or register to begin.')
    display_registration_form("initial_case")

# Footer
st.divider()
st.markdown("<p style='text-align: center; color: grey;'>Made with ❤️ by Ecolytics.</p>", unsafe_allow_html=True)
