# app.py

import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns
from pypfopt import objective_functions
import numpy as np

# --- Helper Functions ---

@st.cache_data # Cache data to avoid re-fetching on every rerun
def fetch_stock_data(tickers, start_date, end_date):
    """Fetches historical adjusted close prices for given tickers."""
    adj_close_data = pd.DataFrame()
    for ticker in tickers:
        try:
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if not data.empty:
                adj_close_data[ticker] = data['Adj Close']
            else:
                st.warning(f"No data found for {ticker} in the specified range. Skipping.")
        except Exception as e:
            st.error(f"Error fetching data for {ticker}: {e}. Skipping.")
    return adj_close_data

def simulate_esg_scores(tickers):
    """
    Simulates ESG scores for a given list of tickers.
    In a real application, this would fetch from an external API.
    """
    # Example placeholder ESG scores (out of 100)
    # You would replace this with actual data integration
    esg_data = {
        "AAPL": 85, "MSFT": 88, "GOOGL": 82, "TSLA": 70,
        "XOM": 35, "NEE": 92, "JPM": 60, "NVDA": 78,
        # Add more if needed, or handle missing ones gracefully
    }
    # Create a Series, reindex to ensure all input tickers are covered, fill missing with a default
    esg_series = pd.Series(esg_data, name="ESG_Score").reindex(tickers, fill_value=50) # Default ESG 50 for unknown
    return esg_series

def maximize_esg_objective(weights, esg_scores_series):
    """
    Custom objective function for PyPortfolioOpt to maximize ESG score.
    PyPortfolioOpt minimizes objectives, so we return the negative sum.
    """
    aligned_esg_scores = esg_scores_series.reindex(weights.index)
    portfolio_esg_score = (weights * aligned_esg_scores).sum()
    return -portfolio_esg_score # Minimize the negative ESG score to maximize ESG

# --- Streamlit App Layout ---

st.set_page_config(layout="wide", page_title="Green Investment Portfolio Optimizer")

st.title("🌱 Green Investment Portfolio Optimizer")
st.markdown("""
    Optimize your investment portfolio considering **financial returns, risk, and ESG (Environmental, Social, Governance) factors**.
    Enter your desired stock tickers and investment amount to get an ESG-aware portfolio allocation.
""")

# --- Sidebar for User Inputs ---
st.sidebar.header("Configuration")

# Ticker Input
default_tickers = "AAPL, MSFT, GOOGL, NEE, XOM, JPM, TSLA, NVDA"
ticker_input = st.sidebar.text_area(
    "Enter Stock Tickers (comma-separated)",
    value=default_tickers,
    help="Example: AAPL, MSFT, GOOGL"
)
tickers = [t.strip().upper() for t in ticker_input.split(',') if t.strip()]

# Investment Amount Input
investment_amount = st.sidebar.number_input(
    "Total Investment Amount ($)",
    min_value=100.0,
    value=10000.0,
    step=100.0,
    format="%.2f",
    help="The total amount of money you want to invest."
)

# Date Range for Historical Data
st.sidebar.subheader("Historical Data Range")
end_date = datetime.date.today()
start_date = st.sidebar.date_input(
    "Start Date",
    value=end_date - datetime.timedelta(days=5*365), # Default to 5 years ago
    max_value=end_date - datetime.timedelta(days=30) # At least 1 month of data
)
st.sidebar.date_input("End Date", value=end_date, disabled=True) # End date is always today

# Optimization Strategy Selection
st.sidebar.subheader("Optimization Strategy")
optimization_strategy = st.sidebar.selectbox(
    "Choose Optimization Goal",
    options=["Maximize Sharpe Ratio (with ESG)", "Target Return (with Max ESG)", "Minimize Volatility (with ESG)"],
    index=0,
    help="""
    **Maximize Sharpe Ratio:** Find the portfolio with the best risk-adjusted return, considering ESG.
    **Target Return:** Find the portfolio that achieves a specific return with the highest ESG score.
    **Minimize Volatility:** Find the portfolio with the lowest risk, considering ESG.
    """
)

target_return_input = 0.15
if optimization_strategy == "Target Return (with Max ESG)":
    target_return_input = st.sidebar.slider(
        "Target Annual Return (%)",
        min_value=0.0,
        max_value=50.0,
        value=15.0,
        step=0.5,
        format="%.1f",
        help="The desired annual return for your portfolio."
    ) / 100.0 # Convert percentage to decimal


# --- Main Content Area ---

if st.button("Optimize Portfolio"):
    if not tickers:
        st.error("Please enter at least one stock ticker.")
    else:
        with st.spinner("Fetching data and optimizing portfolio..."):
            # 1. Fetch Data
            adj_close_data = fetch_stock_data(tickers, start_date, end_date)

            if adj_close_data.empty:
                st.error("Could not fetch valid data for the provided tickers. Please check them and try again.")
            else:
                # Filter out tickers for which no data was fetched
                valid_tickers = adj_close_data.columns.tolist()
                if not valid_tickers:
                    st.error("No valid stock data available for optimization. Please check your ticker list.")
                    st.stop() # Stop execution if no valid tickers

                # 2. Simulate ESG Scores
                esg_series = simulate_esg_scores(valid_tickers)
                # Ensure ESG scores are aligned with the actual data columns
                # Use adj_close_data.columns to ensure correct alignment
                esg_series = esg_series.reindex(adj_close_data.columns)


                # 3. Prepare Data for PyPortfolioOpt
                mu = expected_returns.mean_historical_returns(adj_close_data)
                S = risk_models.sample_cov(adj_close_data)

                # Ensure mu and S are aligned with the tickers that have both financial and ESG data
                common_tickers = list(set(mu.index) & set(S.index) & set(esg_series.index) & set(valid_tickers))
                if not common_tickers:
                    st.error("No common tickers found with both financial data and ESG scores for optimization. Please adjust your ticker list.")
                    st.stop()

                mu = mu[common_tickers]
                S = S.loc[common_tickers, common_tickers]
                esg_series = esg_series[common_tickers]

                # Initialize EfficientFrontier
                ef = EfficientFrontier(mu, S)
                # Add the custom ESG objective (minimize negative ESG)
                ef.add_objective(maximize_esg_objective, esg_scores_series=esg_series)

                # 4. Perform Optimization based on selected strategy
                try:
                    if optimization_strategy == "Maximize Sharpe Ratio (with ESG)":
                        raw_weights = ef.max_sharpe()
                        st.subheader("Optimized Portfolio (Max Sharpe Ratio with ESG)")
                    elif optimization_strategy == "Target Return (with Max ESG)":
                        # Find max return to set realistic bounds for target return
                        ef_max_ret_check = EfficientFrontier(mu, S)
                        # No need to add ESG objective to ef_max_ret_check if just finding max return
                        # However, if you want the max return *considering* ESG, then add it.
                        # For simplicity here, let's just get the theoretical max return from the frontier
                        # without necessarily optimizing for ESG in this check.
                        ef_max_ret_check.add_objective(maximize_esg_objective, esg_scores_series=esg_series) # Keep it consistent
                        # Use efficient_frontier to get the points on the frontier
                        # This will give us a range of returns
                        try:
                            # Try to get the max return from a simple max_sharpe or max_return portfolio
                            # This is a bit tricky as max_return might not always be feasible
                            # A more robust way is to iterate over the efficient frontier.
                            # For simplicity, let's just use the max return from a max_sharpe portfolio as a proxy.
                            test_weights = ef_max_ret_check.max_sharpe()
                            max_possible_return = ef_max_ret_check.portfolio_performance()[0]
                        except Exception:
                            # Fallback if max_sharpe fails (e.g., no valid solution)
                            max_possible_return = mu.max() # Use max individual stock return as a very rough upper bound

                        if target_return_input > max_possible_return:
                            st.warning(f"Target return ({target_return_input*100:.1f}%) is too high. Max possible return is approximately {max_possible_return*100:.1f}%. Adjusting target to max possible.")
                            target_return_input = max_possible_return * 0.95 # Adjust slightly below max
                            if target_return_input < 0: target_return_input = 0.01 # Ensure it's not negative

                        raw_weights = ef.efficient_return(target_return=target_return_input)
                        st.subheader(f"Optimized Portfolio (Target Return: {target_return_input*100:.1f}% with Max ESG)")
                    elif optimization_strategy == "Minimize Volatility (with ESG)":
                        raw_weights = ef.min_volatility()
                        st.subheader("Optimized Portfolio (Minimize Volatility with ESG)")

                    # Clean weights (remove tiny weights, normalize to 1)
                    cleaned_weights = ef.clean_weights()

                    # Calculate performance
                    ret, vol, sharpe = ef.portfolio_performance(verbose=False)

                    # Calculate actual portfolio ESG score
                    portfolio_esg_score = (pd.Series(cleaned_weights) * esg_series.reindex(cleaned_weights.keys())).sum()

                    st.success("Optimization Complete!")

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Expected Annual Return", f"{ret*100:.2f}%")
                    with col2:
                        st.metric("Annual Volatility", f"{vol*100:.2f}%")
                    with col3:
                        st.metric("Sharpe Ratio", f"{sharpe:.2f}")
                    with col4:
                        st.metric("Portfolio ESG Score", f"{portfolio_esg_score:.2f}")

                    st.markdown("---")
                    st.subheader("Portfolio Allocation")

                    # Display weights and allocated amount
                    portfolio_df = pd.DataFrame({
                        "Ticker": list(cleaned_weights.keys()),
                        "Weight": [f"{w*100:.2f}%" for w in cleaned_weights.values()],
                        "Allocated Amount ($)": [f"{w * investment_amount:.2f}" for w in cleaned_weights.values()],
                        "ESG Score (Individual)": [esg_series.get(t, 'N/A') for t in cleaned_weights.keys()]
                    })
                    # Filter out assets with negligible weight
                    portfolio_df['Raw_Weight'] = list(cleaned_weights.values())
                    portfolio_df = portfolio_df[portfolio_df['Raw_Weight'] > 0.001].drop(columns=['Raw_Weight'])
                    st.dataframe(portfolio_df.set_index("Ticker"), use_container_width=True)

                    st.markdown("---")
                    st.subheader("Individual Asset ESG Scores")
                    st.dataframe(esg_series.to_frame(name="ESG Score"), use_container_width=True)

                except Exception as e:
                    st.error(f"An error occurred during optimization: {e}")
                    st.info("This might happen if the target return is unachievable, or if there's insufficient historical data for some tickers. Try adjusting your inputs.")

st.markdown("---")
st.markdown("Developed by Friday for KD. Data from yFinance. ESG scores are simulated for demonstration.")
