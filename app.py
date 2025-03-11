"""
CrewAI Bank Account Agent for Wise - Streamlit App
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import tempfile
import json
import logging
import traceback
from typing import Dict, List, Any, Optional

# Import our modules
from wise.client import WiseClient
from utils.data_processor import (
    process_accounts, 
    process_transactions, 
    categorize_transactions, 
    calculate_summary_stats
)
from utils.export import export_to_json, export_to_pdf, export_to_google_sheets
from agents.financial_agents import FinancialAgents

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page config
st.set_page_config(
    page_title="Wise Account Analysis",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App title and description
st.title("💰 Wise Account Analysis with CrewAI")
st.markdown("""
This app connects to your Wise account (read-only) to analyze your balances and transactions.
Our AI agents will provide personalized financial insights and recommendations.
""")

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = None
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = None
if 'environment' not in st.session_state:
    st.session_state.environment = "sandbox"  # Default to sandbox for testing
if 'accounts_data' not in st.session_state:
    st.session_state.accounts_data = None
if 'transactions_data' not in st.session_state:
    st.session_state.transactions_data = None
if 'summary_stats' not in st.session_state:
    st.session_state.summary_stats = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'export_path' not in st.session_state:
    st.session_state.export_path = None
if 'google_sheets_url' not in st.session_state:
    st.session_state.google_sheets_url = None
if 'analysis_error' not in st.session_state:
    st.session_state.analysis_error = None

# Sidebar for API key input and date range selection
with st.sidebar:
    st.header("Configuration")
    
    # Environment selection
    environment = st.radio(
        "Wise API Environment",
        ["Sandbox", "Production"],
        index=0,  # Default to Sandbox
        help="Select 'Sandbox' for testing with the Wise sandbox environment, or 'Production' for real account data."
    )
    st.session_state.environment = environment.lower()
    
    # Wise API Key input
    wise_api_key = st.text_input(
        f"{environment} API Key", 
        type="password", 
        help=f"Enter your Wise {environment.lower()} API key with read-only permissions"
    )
    
    # OpenAI API Key input
    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Enter your OpenAI API key for AI analysis (required for CrewAI agents)"
    )
    if openai_api_key:
        st.session_state.openai_api_key = openai_api_key
        # Set the environment variable for OpenAI API key
        os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Add a test button for the OpenAI API key
        if st.button("Test OpenAI API Key"):
            try:
                import openai
                from openai import OpenAI
                
                # Simple test call to OpenAI using the new API format
                client = OpenAI(api_key=openai_api_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello, world!"}],
                    max_tokens=5
                )
                st.success("✅ OpenAI API key is valid!")
            except Exception as e:
                st.error(f"❌ Invalid OpenAI API key: {str(e)}")
                logger.error(f"Error testing OpenAI API key: {e}", exc_info=True)
    
    # Date range selection
    st.subheader("Date Range")
    today = datetime.now()
    default_start = today - timedelta(days=90)
    start_date = st.date_input("Start Date", value=default_start)
    end_date = st.date_input("End Date", value=today)
    
    # Connect button
    if st.button("Connect to Wise"):
        if wise_api_key:
            with st.spinner(f"Connecting to Wise {environment} API..."):
                try:
                    # Initialize Wise client with the selected environment
                    client = WiseClient(wise_api_key, environment=st.session_state.environment)
                    
                    # Validate API key
                    if not client.validate_api_key():
                        st.error("Invalid Wise API key. Please check and try again.")
                    else:
                        st.success(f"Successfully connected to Wise {environment} API!")
                        st.session_state.api_key = wise_api_key
                        
                        # Fetch account data
                        accounts_data = client.get_accounts()
                        accounts_df = process_accounts(accounts_data)
                        st.session_state.accounts_data = accounts_df
                        
                        # Fetch transaction data
                        transactions_data = client.get_transactions(
                            interval_start=start_date.strftime("%Y-%m-%d"),
                            interval_end=end_date.strftime("%Y-%m-%d")
                        )
                        transactions_df = process_transactions(transactions_data)
                        categorized_transactions_df = categorize_transactions(transactions_df)
                        st.session_state.transactions_data = categorized_transactions_df
                        
                        # Calculate summary statistics
                        summary_stats = calculate_summary_stats(categorized_transactions_df)
                        st.session_state.summary_stats = summary_stats
                        
                except Exception as e:
                    st.error(f"Error connecting to Wise API: {str(e)}")
                    logger.error(f"Error connecting to Wise API: {e}", exc_info=True)
        else:
            st.warning("Please enter your Wise API key.")
    
    # Export options
    if st.session_state.analysis_results:
        st.subheader("Export Options")
        export_format = st.selectbox("Export Format", ["PDF", "JSON", "Google Sheets"])
        
        if st.button("Export Report"):
            with st.spinner(f"Exporting to {export_format}..."):
                try:
                    # Prepare export data
                    export_data = {
                        "summary": st.session_state.summary_stats,
                        "recommendations": st.session_state.analysis_results.get("recommendations", []),
                        "analysis": st.session_state.analysis_results.get("analysis", ""),
                        "advice": st.session_state.analysis_results.get("advice", ""),
                        "optimization": st.session_state.analysis_results.get("optimization", ""),
                        "transactions": st.session_state.transactions_data.to_dict(orient='records') if not st.session_state.transactions_data.empty else []
                    }
                    
                    if export_format == "PDF":
                        export_path = export_to_pdf(export_data)
                        st.session_state.export_path = export_path
                        st.success(f"Report exported to PDF: {export_path}")
                    
                    elif export_format == "JSON":
                        export_path = export_to_json(export_data)
                        st.session_state.export_path = export_path
                        st.success(f"Report exported to JSON: {export_path}")
                    
                    elif export_format == "Google Sheets":
                        st.error("Google Sheets export requires a credentials file. This feature is disabled in the demo.")
                        # In a real app, you would handle Google Sheets credentials properly
                        # export_path = export_to_google_sheets(export_data, "credentials.json")
                        # st.session_state.google_sheets_url = export_path
                        # st.success(f"Report exported to Google Sheets: [Open Sheet]({export_path})")
                
                except Exception as e:
                    st.error(f"Error exporting report: {str(e)}")
                    logger.error(f"Error exporting report: {e}", exc_info=True)

# Main content area
if st.session_state.api_key:
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Dashboard", "Transactions", "AI Analysis"])
    
    # Dashboard tab
    with tab1:
        st.header("Financial Dashboard")
        
        # Account balances
        if st.session_state.accounts_data is not None and not st.session_state.accounts_data.empty:
            st.subheader("Account Balances")
            
            # Create a bar chart for account balances
            fig_balances = px.bar(
                st.session_state.accounts_data,
                x='currency',
                y='balance',
                color='currency',
                title="Account Balances by Currency",
                labels={'balance': 'Balance', 'currency': 'Currency'}
            )
            st.plotly_chart(fig_balances, use_container_width=True)
            
            # Display account details in a table
            st.dataframe(st.session_state.accounts_data, use_container_width=True)
        
        # Summary statistics
        if st.session_state.summary_stats:
            st.subheader("Financial Summary")
            
            # Create columns for key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Income", f"${st.session_state.summary_stats['total_income']:.2f}")
            
            with col2:
                st.metric("Total Expenses", f"${st.session_state.summary_stats['total_expenses']:.2f}")
            
            with col3:
                net_cashflow = st.session_state.summary_stats['net_cashflow']
                delta_color = "normal" if net_cashflow >= 0 else "inverse"
                st.metric("Net Cashflow", f"${net_cashflow:.2f}", delta=f"{net_cashflow:.2f}", delta_color=delta_color)
            
            with col4:
                st.metric("Avg. Daily Expense", f"${st.session_state.summary_stats['avg_daily_expense']:.2f}")
            
            # Monthly summary chart
            monthly_data = st.session_state.summary_stats.get('monthly_summary', [])
            if monthly_data:
                st.subheader("Monthly Income vs. Expenses")
                
                # Convert to DataFrame for plotting
                monthly_df = pd.DataFrame(monthly_data)
                
                # Create a grouped bar chart
                fig_monthly = go.Figure()
                
                fig_monthly.add_trace(go.Bar(
                    x=monthly_df['month'],
                    y=monthly_df['income'],
                    name='Income',
                    marker_color='green'
                ))
                
                fig_monthly.add_trace(go.Bar(
                    x=monthly_df['month'],
                    y=monthly_df['expenses'],
                    name='Expenses',
                    marker_color='red'
                ))
                
                fig_monthly.add_trace(go.Scatter(
                    x=monthly_df['month'],
                    y=monthly_df['net'],
                    name='Net',
                    mode='lines+markers',
                    line=dict(color='blue', width=2)
                ))
                
                fig_monthly.update_layout(
                    title='Monthly Income vs. Expenses',
                    xaxis_title='Month',
                    yaxis_title='Amount',
                    barmode='group'
                )
                
                st.plotly_chart(fig_monthly, use_container_width=True)
            
            # Top expense categories pie chart
            top_expenses = st.session_state.summary_stats.get('top_expense_categories', {})
            if top_expenses:
                st.subheader("Top Expense Categories")
                
                # Convert to DataFrame for plotting
                expense_df = pd.DataFrame({
                    'category': list(top_expenses.keys()),
                    'amount': [abs(amount) for amount in top_expenses.values()]
                })
                
                # Create a pie chart
                fig_expenses = px.pie(
                    expense_df,
                    values='amount',
                    names='category',
                    title='Top Expense Categories',
                    hole=0.4
                )
                
                st.plotly_chart(fig_expenses, use_container_width=True)
    
    # Transactions tab
    with tab2:
        st.header("Transaction History")
        
        if st.session_state.transactions_data is not None and not st.session_state.transactions_data.empty:
            # Filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Category filter
                categories = ['All'] + sorted(st.session_state.transactions_data['custom_category'].unique().tolist())
                selected_category = st.selectbox("Filter by Category", categories)
            
            with col2:
                # Direction filter (income/expense)
                directions = ['All', 'income', 'expense']
                selected_direction = st.selectbox("Filter by Direction", directions)
            
            with col3:
                # Amount filter
                min_amount = float(st.session_state.transactions_data['amount'].min())
                max_amount = float(st.session_state.transactions_data['amount'].max())
                amount_range = st.slider("Amount Range", min_amount, max_amount, (min_amount, max_amount))
            
            # Apply filters
            filtered_df = st.session_state.transactions_data.copy()
            
            if selected_category != 'All':
                filtered_df = filtered_df[filtered_df['custom_category'] == selected_category]
            
            if selected_direction != 'All':
                filtered_df = filtered_df[filtered_df['direction'] == selected_direction]
            
            filtered_df = filtered_df[(filtered_df['amount'] >= amount_range[0]) & (filtered_df['amount'] <= amount_range[1])]
            
            # Display transactions
            st.dataframe(filtered_df, use_container_width=True)
            
            # Transaction timeline
            st.subheader("Transaction Timeline")
            
            # Group by date and calculate daily totals
            daily_df = filtered_df.groupby(filtered_df['date'].dt.date).agg({
                'amount': 'sum'
            }).reset_index()
            
            # Create a line chart
            fig_timeline = px.line(
                daily_df,
                x='date',
                y='amount',
                title='Daily Transaction Amounts',
                labels={'date': 'Date', 'amount': 'Amount'}
            )
            
            st.plotly_chart(fig_timeline, use_container_width=True)
    
    # AI Analysis tab
    with tab3:
        st.header("AI Financial Analysis")
        
        if not st.session_state.openai_api_key:
            st.warning("⚠️ OpenAI API key is required for AI analysis. Please enter your OpenAI API key in the sidebar.")
            
            # Add information about getting an OpenAI API key
            with st.expander("How to get an OpenAI API key"):
                st.markdown("""
                1. Go to [OpenAI's website](https://platform.openai.com/signup)
                2. Create an account or sign in
                3. Navigate to the API section
                4. Create a new API key
                5. Copy the key and paste it in the sidebar
                
                Note: OpenAI API usage may incur charges based on your usage.
                """)
        elif not st.session_state.analysis_results:
            # Check if we have enough data for analysis
            if st.session_state.accounts_data is None or st.session_state.accounts_data.empty:
                st.warning("No account data available. Please connect to Wise first.")
            elif st.session_state.transactions_data is None or st.session_state.transactions_data.empty:
                st.warning("No transaction data available. Please connect to Wise first.")
            else:
                # Add information about CrewAI
                st.info("""
                The AI analysis uses CrewAI to create a team of specialized AI agents:
                - **Financial Data Analyst**: Analyzes patterns and trends in your transaction data
                - **Financial Advisor**: Provides personalized financial advice
                - **Budget Optimizer**: Identifies opportunities to optimize your spending
                
                Click the button below to start the analysis. This may take a few minutes.
                """)
                
                # Add a note about OpenAI API usage
                st.warning("""
                **Note**: This analysis uses the OpenAI API, which may incur charges based on your usage.
                Make sure you have sufficient credits in your OpenAI account.
                """)
                
                if st.button("Generate AI Analysis"):
                    with st.spinner("Our AI agents are analyzing your financial data... This may take a few minutes."):
                        try:
                            # Create financial agents
                            financial_agents = FinancialAgents(
                                st.session_state.accounts_data,
                                st.session_state.transactions_data,
                                st.session_state.summary_stats,
                                openai_api_key=st.session_state.openai_api_key
                            )
                            
                            # Run analysis
                            analysis_results = financial_agents.run_analysis()
                            st.session_state.analysis_results = analysis_results
                            
                            # Check if there was an error
                            if analysis_results.get("analysis", "").startswith("Error during analysis:"):
                                st.session_state.analysis_error = True
                                st.error("There was an error generating the analysis. See details below.")
                            else:
                                st.session_state.analysis_error = False
                                st.success("Analysis complete!")
                            
                            # Force a rerun to show the results
                            st.rerun()
                        except Exception as e:
                            error_msg = str(e)
                            stack_trace = traceback.format_exc()
                            st.error(f"Error generating analysis: {error_msg}")
                            with st.expander("View error details"):
                                st.code(stack_trace)
                            logger.error(f"Error generating analysis: {e}", exc_info=True)
                            st.session_state.analysis_error = True
        
        if st.session_state.analysis_results:
            # If there was an error, display it prominently
            if st.session_state.analysis_error:
                st.error("There was an error generating the analysis. Please check your OpenAI API key and try again.")
                
                with st.expander("Error Details"):
                    st.markdown(st.session_state.analysis_results.get("analysis", "Unknown error"))
                
                # Add a button to regenerate the analysis
                if st.button("Try Again"):
                    st.session_state.analysis_results = None
                    st.session_state.analysis_error = None
                    st.rerun()
            else:
                # Display analysis results
                st.subheader("Data Analysis")
                with st.expander("View Data Analysis", expanded=True):
                    st.markdown(st.session_state.analysis_results.get("analysis", "No analysis available."))
                
                st.subheader("Financial Advice")
                with st.expander("View Financial Advice", expanded=True):
                    st.markdown(st.session_state.analysis_results.get("advice", "No advice available."))
                
                st.subheader("Budget Optimization")
                with st.expander("View Budget Optimization", expanded=True):
                    st.markdown(st.session_state.analysis_results.get("optimization", "No optimization plan available."))
                
                # Display recommendations
                st.subheader("Key Recommendations")
                recommendations = st.session_state.analysis_results.get("recommendations", [])
                
                if recommendations:
                    for i, rec in enumerate(recommendations, 1):
                        st.markdown(f"**{i}.** {rec}")
                else:
                    st.info("No recommendations available.")
                
                # Add a button to regenerate the analysis if needed
                if st.button("Regenerate Analysis"):
                    st.session_state.analysis_results = None
                    st.session_state.analysis_error = None
                    st.rerun()

else:
    # Display instructions when not connected
    st.info("👈 Enter your Wise API key in the sidebar to get started.")
    
    # How to get API key instructions
    st.header("How to Get Your Wise API Key")
    
    # Different instructions based on selected environment
    if st.session_state.environment == "sandbox":
        st.markdown("""
        ### Sandbox Environment
        
        1. Sign up for a Wise developer account at [https://sandbox.transferwise.tech/register](https://sandbox.transferwise.tech/register)
        2. Create a new API token with read-only permissions
        3. Copy the token and use it in this application
        
        The sandbox environment allows you to test the application without using real account data.
        """)
    else:
        st.markdown("""
        ### Production Environment
        
        1. Log in to your Wise account
        2. Go to Settings > API tokens
        3. Create a new token with read-only permissions
        4. Copy the token and use it in this application
        """)
    
    st.markdown("""
    **Note:** Your API key is only stored temporarily in the Streamlit session state and is never persisted to disk.
    All data processing happens locally on your machine.
    """)
    
    # OpenAI API key instructions
    st.header("OpenAI API Key (Required for AI Analysis)")
    st.markdown("""
    To use the AI analysis features, you'll need an OpenAI API key:
    
    1. Go to [OpenAI's website](https://platform.openai.com/signup)
    2. Create an account or sign in
    3. Navigate to the API section
    4. Create a new API key
    5. Copy the key and paste it in the sidebar
    
    Note: OpenAI API usage may incur charges based on your usage.
    """)
    
    # Sample dashboard image
    st.header("Sample Dashboard")
    st.image("https://via.placeholder.com/800x400?text=Sample+Wise+Dashboard", use_container_width=True)

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using CrewAI and Streamlit") 