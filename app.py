import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import json # For JSON export

# --- Page Configuration ---
st.set_page_config(
    page_title="GreenInvest Analytics",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MOCK DATABASE & HELPER FUNCTIONS ---
FINANCE_OPPORTUNITIES = [
    {"name": "GreenStart Grant Program", "type": "Grant", "description": "A grant for businesses starting their sustainability journey. Covers up to 50% of the cost for an initial energy audit.", "minimum_esg_score": 0, "icon": "🌱", "url": "https://www.sba.gov/funding-programs/grants"},
    {"name": "Eco-Efficiency Business Loan", "type": "Loan", "description": "Low-interest loans for SMEs investing in energy-efficient equipment or renewable energy installations.", "minimum_esg_score": 60, "icon": "💡", "url": "https://www.bankofamerica.com/smallbusiness/business-financing/"},
    {"name": "Sustainable Supply Chain Fund", "type": "Venture Capital", "description": "Equity investment for companies demonstrating strong ESG performance and a commitment to a sustainable supply chain.", "minimum_esg_score": 75, "icon": "🤝", "url": "https://www.blackrock.com/corporate/sustainability"},
    {"name": "Circular Economy Innovators Fund", "type": "Venture Capital", "description": "Seed funding for businesses pioneering models in waste reduction, recycling, and resource circularity.", "minimum_esg_score": 80, "icon": "♻️", "url": "https://www.closedlooppartners.com/"},
    {"name": "Impact Investors Alliance - Premier Partner", "type": "Private Equity", "description": "For top-tier ESG performers. Provides significant growth capital and access to a global network of sustainable businesses.", "minimum_esg_score": 90, "icon": "🏆", "url": "https://thegiin.org/"}
]

# Mock Industry Benchmark Data (for benchmarking feature)
INDUSTRY_AVERAGES = {
    'Environmental': 70,
    'Social': 65,
    'Governance': 75,
    'Overall ESG': 70
}

# CO2 Emission Factors (Simplified for demonstration)
CO2_EMISSION_FACTORS = {
    'energy_kwh_to_co2': 0.4, # kg CO2e per kWh (avg grid mix)
    'water_m3_to_co2': 0.1,  # kg CO2e per m3 water (from treatment/supply)
    'waste_kg_to_co2': 0.5   # kg CO2e per kg waste (assuming landfill)
}

def calculate_esg_score(env_data, social_data, gov_data):
    weights = {'E': 0.4, 'S': 0.3, 'G': 0.3}
    # Environmental Score: Higher is better. Normalizing and averaging.
    e_score = (max(0, 100 - (env_data['energy'] / 1000)) + # Lower energy is better
               max(0, 100 - (env_data['water'] / 500)) +   # Lower water is better
               max(0, 100 - (env_data['waste'] / 100)) +    # Lower waste is better
               env_data['recycling']) / 4                    # Higher recycling is better

    # Social Score: Higher is better.
    s_score = (max(0, 100 - (social_data['turnover'] * 2)) + # Lower turnover is better
               max(0, 100 - (social_data['incidents'] * 10)) + # Lower incidents is better
               social_data['diversity']) / 3                  # Higher diversity is better

    # Governance Score: Higher is better.
    g_score = (gov_data['independence'] + gov_data['ethics']) / 2 # Direct percentage values
    
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
    energy_co2 = env_data['energy'] * CO2_EMISSION_FACTORS['energy_kwh_to_co2']
    water_co2 = env_data['water'] * CO2_EMISSION_FACTORS['water_m3_to_co2']
    waste_co2 = env_data['waste'] * CO2_EMISSION_FACTORS['waste_kg_to_co2']
    total_co2 = energy_co2 + water_co2 + waste_co2
    return {
        'total_co2_kg': total_co2,
        'energy_co2_kg': energy_co2,
        'water_co2_kg': water_co2,
        'waste_co2_kg': waste_co2
    }

# --- Initialize session state for historical data ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_esg_data' not in st.session_state:
    st.session_state.current_esg_data = None # Store the most recently calculated data

# --- Function to display the full dashboard ---
def display_dashboard(final_score, e_score, s_score, g_score, env_data):
    st.header("Your ESG Performance Dashboard")

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

        # Metric Cards for E, S, G scores
        col_e_card, col_s_card, col_g_card = st.columns(3)
        with col_e_card:
            with st.container(border=True):
                st.metric("🌳 Environmental", f"{e_score:.1f}")
        with col_s_card:
            with st.container(border=True):
                st.metric("❤️ Social", f"{s_score:.1f}")
        with col_g_card:
            with st.container(border=True):
                st.metric("⚖️ Governance", f"{g_score:.1f}")

        st.divider()

        # Environmental Impact Estimation
        impact_data = calculate_environmental_impact(env_data)
        st.subheader("🌍 Environmental Impact Estimation")
        st.info(f"Based on your environmental data, your estimated annual **CO2 equivalent emissions are {impact_data['total_co2_kg']:.2f} kg**.")
        st.markdown(f"- Energy-related CO2: {impact_data['energy_co2_kg']:.2f} kg")
        st.markdown(f"- Water-related CO2: {impact_data['water_co2_kg']:.2f} kg")
        st.markdown(f"- Waste-related CO2: {impact_data['waste_co2_kg']:.2f} kg")
        
        st.divider()

        # Charts
        col1, col2 = st.columns(2)
        with col1:
            fig_spider = go.Figure()
            fig_spider.add_trace(go.Scatterpolar(r=[e_score, s_score, g_score, e_score], theta=['Environmental', 'Social', 'Governance', 'Environmental'], fill='toself', name='Your Score', line_color=st.get_option('theme.primaryColor'))) # Use theme color
            # Benchmarking trace
            fig_spider.add_trace(go.Scatterpolar(r=[INDUSTRY_AVERAGES['Environmental'], INDUSTRY_AVERAGES['Social'], INDUSTRY_AVERAGES['Governance'], INDUSTRY_AVERAGES['Environmental']], theta=['Environmental', 'Social', 'Governance', 'Environmental'], fill='none', name='Industry Average', line_color='grey', line_dash='dot'))
            fig_spider.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=True, # Show legend for benchmarking
                title="ESG Balanced Scorecard",
                height=350,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_spider, use_container_width=True)
        with col2:
            fig_bar = go.Figure(go.Bar(x=[e_score, s_score, g_score], y=['Environmental', 'Social', 'Governance'], orientation='h',
                                       marker_color=['#4CAF50', '#8BC34A', '#CDDC39']))
            fig_bar.update_layout(title="Score Breakdown", xaxis_title="Score (out of 100)", height=350)
            st.plotly_chart(fig_bar, use_container_width=True)

        if final_score > 85:
            st.balloons()
            st.success("Congratulations! Your high ESG score is outstanding and unlocks premium opportunities. Keep up the great work, KD!")

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
                    st.link_button(f"Apply Now {opp['icon']}", opp['url']) # Modified: Added icon to button

    with tab4: # New: Historical Trends Tab
        st.header("🕰️ Your ESG Performance History")
        if not st.session_state.history:
            st.info("No historical data available yet. Calculate your score and save it to build a trend.")
        else:
            history_df = pd.DataFrame(st.session_state.history)
            
            # Line chart for Overall ESG Score over time
            fig_history_overall = go.Figure()
            fig_history_overall.add_trace(go.Scatter(x=history_df['timestamp'], y=history_df['overall_score'], mode='lines+markers', name='Overall Score', line_color=st.get_option('theme.primaryColor')))
            fig_history_overall.update_layout(title="Overall ESG Score Over Time", xaxis_title="Date", yaxis_title="Score (0-100)")
            st.plotly_chart(fig_history_overall, use_container_width=True)

            # Line chart for E, S, G scores over time
            fig_history_esg = go.Figure()
            fig_history_esg.add_trace(go.Scatter(x=history_df['timestamp'], y=history_df['e_score'], mode='lines+markers', name='Environmental', line_color='#4CAF50'))
            fig_history_esg.add_trace(go.Scatter(x=history_df['timestamp'], y=history_df['s_score'], mode='lines+markers', name='Social', line_color='#8BC34A'))
            fig_history_esg.add_trace(go.Scatter(x=history_df['timestamp'], y=history_df['g_score'], mode='lines+markers', name='Governance', line_color='#CDDC39'))
            fig_history_esg.update_layout(title="ESG Category Scores Over Time", xaxis_title="Date", yaxis_title="Score (0-100)")
            st.plotly_chart(fig_history_esg, use_container_width=True)

            st.subheader("Raw Historical Data")
            st.dataframe(history_df.set_index('timestamp').sort_index(ascending=False))

    with tab5: # New: Scenario Planner Tab
        st.header("🧪 Scenario Planner: What If...?")
        st.write("Adjust the metrics below to see how your ESG score and opportunities would change.")

        if st.session_state.current_esg_data is None:
            st.warning("Please calculate your initial ESG score first to populate the scenario planner.")
        else:
            current_data = st.session_state.current_esg_data
            
            st.subheader("Adjust Metrics for Scenario")
            col_s1, col_s2, col_s3 = st.columns(3)

            with col_s1:
                st.markdown("##### 🌳 Environmental")
                scenario_energy = st.number_input("Energy Consumption (kWh)", min_value=0, value=current_data['env']['energy'], key='scenario_energy')
                scenario_water = st.number_input("Water Usage (m³)", min_value=0, value=current_data['env']['water'], key='scenario_water')
                scenario_waste = st.number_input("Waste Generated (kg)", min_value=0, value=current_data['env']['waste'], key='scenario_waste')
                scenario_recycling = st.slider("Recycling Rate (%)", min_value=0, max_value=100, value=current_data['env']['recycling'], key='scenario_recycling')
            
            with col_s2:
                st.markdown("##### ❤️ Social")
                scenario_turnover = st.slider("Employee Turnover Rate (%)", min_value=0, max_value=100, value=current_data['social']['turnover'], key='scenario_turnover')
                scenario_incidents = st.number_input("Safety Incidents", min_value=0, value=current_data['social']['incidents'], key='scenario_incidents')
                scenario_diversity = st.slider("Management Diversity (%)", min_value=0, max_value=100, value=current_data['social']['diversity'], key='scenario_diversity')

            with col_s3:
                st.markdown("##### ⚖️ Governance")
                scenario_independence = st.slider("Board Independence (%)", min_value=0, max_value=100, value=current_data['gov']['independence'], key='scenario_independence')
                scenario_ethics = st.slider("Ethics Training Completion (%)", min_value=0, max_value=100, value=current_data['gov']['ethics'], key='scenario_ethics')

            scenario_env_data = {'energy': scenario_energy, 'water': scenario_water, 'waste': scenario_waste, 'recycling': scenario_recycling}
            scenario_social_data = {'turnover': scenario_turnover, 'incidents': scenario_incidents, 'diversity': scenario_diversity}
            scenario_gov_data = {'independence': scenario_independence, 'ethics': scenario_ethics}
            
            scenario_final_score, scenario_e_score, scenario_s_score, scenario_g_score = calculate_esg_score(scenario_env_data, scenario_social_data, scenario_gov_data)

            st.subheader("Projected Scenario Results")
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.metric("Projected Overall ESG Score", f"{scenario_final_score:.1f}")
                st.metric("Projected Environmental Score", f"{scenario_e_score:.1f}")
                st.metric("Projected Social Score", f"{scenario_s_score:.1f}")
                st.metric("Projected Governance Score", f"{scenario_g_score:.1f}")
            with col_res2:
                st.markdown("##### Projected Unlocked Opportunities")
                scenario_unlocked_opportunities = get_financial_opportunities(scenario_final_score)
                if not scenario_unlocked_opportunities:
                    st.warning("No opportunities unlocked in this scenario. Try improving metrics further!")
                else:
                    for opp in scenario_unlocked_opportunities:
                        st.markdown(f"- {opp['icon']} {opp['name']} (Min ESG: {opp['minimum_esg_score']})")

    st.divider() # Divider before the download button and footer

    # Export Report
    if final_score is not None:
        report_data = {
            "Overall_ESG_Score": f"{final_score:.1f}",
            "Environmental_Score": f"{e_score:.1f}",
            "Social_Score": f"{s_score:.1f}",
            "Governance_Score": f"{g_score:.1f}",
            "Input_Data": {
                "Environmental": {
                    "Energy_Consumption_kWh": env_data['energy'],
                    "Water_Usage_m3": env_data['water'],
                    "Waste_Generation_kg": env_data['waste'],
                    "Recycling_Rate_pct": env_data['recycling']
                },
                "Social": {
                    "Employee_Turnover_pct": social_data['turnover'],
                    "Safety_Incidents_count": social_data['incidents'],
                    "Management_Diversity_pct": social_data['diversity']
                },
                "Governance": {
                    "Board_Independence_pct": gov_data['independence'],
                    "Ethics_Training_pct": gov_data['ethics']
                }
            },
            "Environmental_Impact_Estimation": calculate_environmental_impact(env_data),
            "Recommendations_Environmental": recommendations['E'],
            "Recommendations_Social": recommendations['S'],
            "Recommendations_Governance": recommendations['G'],
            "Unlocked_Financial_Opportunities": [{"name": opp['name'], "type": opp['type'], "min_esg": opp['minimum_esg_score']} for opp in unlocked_opportunities],
            "Industry_Benchmark_Averages": INDUSTRY_AVERAGES
        }
        json_report = json.dumps(report_data, indent=4)
        st.download_button(
            label="Download Full ESG Report (JSON) 📥",
            data=json_report,
            file_name="greeninvest_esg_report.json",
            mime="application/json",
            use_container_width=True
        )


# --- UI ---
st.title("🌿 GreenInvest Analytics")
st.markdown("An interactive tool for SMEs to measure, improve, and report on their ESG performance to unlock green finance opportunities.")

# --- Sidebar ---
st.sidebar.header("Step 1: Choose Input Method")
st.sidebar.divider()
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
        energy_consumption = st.number_input(
            "Annual Energy Consumption (kWh)",
            min_value=0,
            value=50000,
            help="Total electricity, natural gas, and other fuel consumption in kilowatt-hours (kWh) over the past year."
        )
        water_usage = st.number_input(
            "Annual Water Usage (cubic meters)",
            min_value=0,
            value=2500,
            help="Total water consumed in cubic meters (m³) over the past year."
        )
        waste_generation = st.number_input(
            "Annual Waste Generated (kg)",
            min_value=0,
            value=1000,
            help="Total solid waste generated in kilograms (kg) annually."
        )
        recycling_rate = st.slider(
            "Recycling Rate (%)",
            min_value=0, max_value=100, value=40,
            help="Percentage of total waste that is recycled."
        )
    with st.sidebar.expander("❤️ Social", expanded=True):
        employee_turnover = st.slider(
            "Employee Turnover Rate (%)",
            min_value=0, max_value=100, value=15,
            help="Percentage of employees leaving the company annually."
        )
        safety_incidents = st.number_input(
            "Number of Safety Incidents",
            min_value=0, value=3,
            help="Total number of reported workplace safety incidents annually."
        )
        diversity_ratio = st.slider(
            "Management Diversity (%)",
            min_value=0, max_value=100, value=30,
            help="Percentage of management positions held by individuals from diverse backgrounds."
        )
    with st.sidebar.expander("⚖️ Governance", expanded=True):
        board_independence = st.slider(
            "Board Independence (%)",
            min_value=0, max_value=100, value=50,
            help="Percentage of independent directors on your company's board."
        )
        ethics_training = st.slider(
            "Ethics Training Completion (%)",
            min_value=0, max_value=100, value=85,
            help="Percentage of employees who have completed ethics training annually."
        )
    
    if st.sidebar.button("Calculate ESG Score", type="primary", use_container_width=True):
        env_data = {'energy': energy_consumption, 'water': water_usage, 'waste': waste_generation, 'recycling': recycling_rate}
        social_data = {'turnover': employee_turnover, 'incidents': safety_incidents, 'diversity': diversity_ratio}
        gov_data = {'independence': board_independence, 'ethics': ethics_training}
        
        final_score, e_score, s_score, g_score = calculate_esg_score(env_data, social_data, gov_data)
        
        # Store current data in session state for scenario and history
        st.session_state.current_esg_data = {
            'env': env_data,
            'social': social_data,
            'gov': gov_data
        }
        st.session_state.history.append({
            'timestamp': pd.to_datetime('today'), # Use actual timestamp for history
            'overall_score': final_score,
            'e_score': e_score,
            's_score': s_score,
            'g_score': g_score
        })
        
        display_dashboard(final_score, e_score, s_score, g_score, env_data)
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
        with st.spinner('Processing your data...'): # Loading spinner
            try:
                data_df = pd.read_csv(uploaded_file)
                # Convert the two-column format to a dictionary
                data_dict = pd.Series(data_df.value.values, index=data_df.metric).to_dict()

                # Extract data
                env_data = {
                    'energy': data_dict.get('energy_consumption_kwh', 0),
                    'water': data_dict.get('water_usage_m3', 0),
                    'waste': data_dict.get('waste_generation_kg', 0),
                    'recycling': data_dict.get('recycling_rate_pct', 0)
                }
                social_data = {
                    'turnover': data_dict.get('employee_turnover_pct', 0),
                    'incidents': data_dict.get('safety_incidents_count', 0),
                    'diversity': data_dict.get('management_diversity_pct', 0)
                }
                gov_data = {
                    'independence': data_dict.get('board_independence_pct', 0),
                    'ethics': data_dict.get('ethics_training_pct', 0)
                }
                
                st.sidebar.success("File uploaded and processed successfully!")
                
                # Calculate and display
                final_score, e_score, s_score, g_score = calculate_esg_score(env_data, social_data, gov_data)

                # Store current data in session state for scenario and history
                st.session_state.current_esg_data = {
                    'env': env_data,
                    'social': social_data,
                    'gov': gov_data
                }
                st.session_state.history.append({
                    'timestamp': pd.to_datetime('today'), # Use actual timestamp for history
                    'overall_score': final_score,
                    'e_score': e_score,
                    's_score': s_score,
                    'g_score': g_score
                })
                
                display_dashboard(final_score, e_score, s_score, g_score, env_data)

            except KeyError as ke:
                st.error(f"Missing expected metric in CSV: {ke}. Please check the template file.")
                st.warning("Ensure your CSV file contains all the required 'metric' names as in the template.")
            except Exception as e:
                st.error(f"An error occurred processing the file: {e}")
                st.warning("Please make sure your CSV file follows the format of the template.")
    else:
        st.info("Upload a CSV file using the sidebar to see your ESG analysis.")

st.divider()
st.write("Made with ❤️ for a greener future. – Friday")
