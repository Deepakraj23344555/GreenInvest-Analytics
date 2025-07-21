import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns
from pypfopt import plotting

# --- Configuration ---
st.set_page_config(layout="wide", page_title="Green Investment Portfolio Optimizer")

# --- Helper Functions ---

@st.cache_data
def get_stock_data(tickers, start_date, end_date):
    """Fetches historical stock data for given tickers."""
    data = yf.download(tickers, start=start_date, end=end_date, progress=False)
    if 'Adj Close' in data.columns:
        # If multiple tickers, 'Adj Close' will be a DataFrame
        if isinstance(data['Adj Close'], pd.DataFrame):
            return data['Adj Close']
        # If single ticker, 'Adj Close' will be a Series
        else:
            return data['Adj Close'].to_frame()
    return pd.DataFrame() # Return empty DataFrame if no 'Adj Close'

def calculate_portfolio_metrics(weights, expected_returns_annual, cov_matrix_annual):
    """Calculates portfolio annual return, volatility, and Sharpe ratio."""
    portfolio_return = np.sum(weights * expected_returns_annual) * 252 # Daily to Annual
    portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix_annual, weights))) * np.sqrt(252) # Daily to Annual
    sharpe_ratio = portfolio_return / portfolio_volatility # Assuming risk-free rate is 0 for simplicity
    return portfolio_return, portfolio_volatility, sharpe_ratio

# --- Streamlit UI ---

st.title("🌱 Green Investment Portfolio Optimizer (Advanced Version)")
st.markdown("""
    Optimize your investment portfolio considering financial returns and sustainability factors.
    **Note:** ESG and Carbon data are simulated for demonstration.
""")

# Sidebar for user inputs
st.sidebar.header("Portfolio Settings")

# Default tickers for demonstration
default_tickers = "AAPL, MSFT, GOOGL, AMZN, TSLA, JPM, XOM, NEE, VWS.CO, ORSTED.CO"
tickers_input = st.sidebar.text_area(
    "Enter stock tickers (comma-separated)",
    value=default_tickers
)
tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]

start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("2024-12-31"))

# --- Portfolio Optimization ---
if st.sidebar.button("Optimize Portfolio"):
    if not tickers:
        st.error("Please enter at least one stock ticker.")
    else:
        with st.spinner("Fetching data and optimizing portfolio..."):
            # Fetch data
            df = get_stock_data(tickers, start_date, end_date)

            if df.empty or df.isnull().values.any():
                st.error("Could not fetch data for all tickers or data contains missing values. Please check tickers and date range.")
                st.stop()

            # Calculate expected returns and covariance matrix
            mu = expected_returns.mean_historical_return(df)
            S = risk_models.sample_cov(df)

            # --- Mean-Variance Optimization (Max Sharpe Ratio) ---
            st.subheader("📊 Portfolio Optimization Results (Max Sharpe Ratio)")
            try:
                ef = EfficientFrontier(mu, S)
                raw_weights = ef.max_sharpe()
                cleaned_weights = ef.clean_weights()

                st.write("Optimized Weights:")
                weights_df = pd.DataFrame.from_dict(cleaned_weights, orient='index', columns=['Weight'])
                weights_df['Weight'] = weights_df['Weight'].map(lambda x: f"{x:.2%}")
                st.dataframe(weights_df)

                # Calculate and display performance metrics
                ret, vol, sharpe = ef.portfolio_performance(verbose=False)
                st.write(f"**Expected Annual Return:** {ret:.2%}")
                st.write(f"**Annual Volatility:** {vol:.2%}")
                st.write(f"**Sharpe Ratio:** {sharpe:.2f}")

                # Plotting the Efficient Frontier (optional, but good for visualization)
                st.subheader("Efficient Frontier")
                fig, ax = plotting.plot_efficient_frontier(ef, show_assets=True)
                st.pyplot(fig)

            except Exception as e:
                st.error(f"Error during optimization: {e}. This might be due to insufficient data or highly correlated assets.")
                st.info("Try adjusting the date range or selecting different tickers.")

# --- Placeholder for ESG and Carbon Features ---
st.header("🌱 ESG and Carbon Impact (Simulated Data)")
st.info("This section will be enhanced to include real ESG and Carbon data integration.")

if st.sidebar.button("Show Simulated ESG/Carbon Data"):
    if not tickers:
        st.warning("Please enter tickers to simulate ESG/Carbon data.")
    else:
        st.subheader("Simulated ESG Scorecard per Asset")
        esg_scores = {ticker: round(np.random.uniform(30, 90), 2) for ticker in tickers}
        esg_df = pd.DataFrame.from_dict(esg_scores, orient='index', columns=['ESG Score (0-100)'])
        st.dataframe(esg_df.sort_values(by='ESG Score (0-100)', ascending=False))

        st.subheader("Simulated Carbon Footprint per Investment")
        carbon_footprints = {ticker: round(np.random.uniform(50, 500), 2) for ticker in tickers} # e.g., tonnes CO2e per $M revenue
        carbon_df = pd.DataFrame.from_dict(carbon_footprints, orient='index', columns=['Carbon Footprint (tCO2e/M$)'])
        st.dataframe(carbon_df.sort_values(by='Carbon Footprint (tCO2e/M$)', ascending=True))

        st.subheader("Scenario Analysis (e.g., Fossil Fuel Divestment)")
        st.write("Imagine you want to divest from high-carbon intensity sectors.")
        st.markdown("""
            This feature would allow you to:
            * Exclude certain industries or companies based on ESG/carbon criteria.
            * Re-optimize the portfolio after applying divestment rules.
            * Compare the financial and sustainability impact of different scenarios.
        """)
        # Example: If 'XOM' (ExxonMobil) is in the list, show a divestment impact
        if 'XOM' in tickers:
            st.warning("Scenario: If XOM (a fossil fuel company) were divested, how would your portfolio change?")
            st.write("In a real scenario, we would re-run optimization excluding XOM and show new metrics.")
        else:
            st.write("No typical fossil fuel companies detected in your current tickers for divestment scenario demonstration.")

# --- Placeholder for Download and Tracking ---
st.header("📥 Portfolio Download & Tracking (Coming Soon with SQLite)")
st.info("""
    This section will allow you to:
    * Download your optimized portfolio as a CSV or Excel file.
    * Save your portfolio to a local SQLite database for historical tracking.
    * View past portfolio performance and compare against benchmarks.
""")

# --- Instructions to Run ---
st.sidebar.markdown("---")
st.sidebar.markdown("### How to Run:")
st.sidebar.markdown("1. Save the code above as `streamlit_app.py`.")
st.sidebar.markdown("2. Save the `requirements.txt` file.")
st.sidebar.markdown("3. Open your terminal in the same directory.")
st.sidebar.markdown("4. Run `pip install -r requirements.txt`")
st.sidebar.markdown("5. Run `streamlit run streamlit_app.py`")

