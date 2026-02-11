"""
Edmonton Transit System Real-Time Analytics Dashboard
Main Streamlit application.
"""
import sys
from pathlib import Path

# Ensure dashboard directory is on path so 'components' and 'data_loader' resolve
_dashboard_dir = Path(__file__).resolve().parent
if str(_dashboard_dir) not in sys.path:
    sys.path.insert(0, str(_dashboard_dir))

import streamlit as st
import pandas as pd
from datetime import datetime
import time

from components.kpi_cards import render_kpi_cards
from components.delay_heatmap import render_delay_heatmap
from components.route_performance import render_route_performance
from components.live_map import render_live_map
from data_loader import load_dashboard_data


# Page configuration
st.set_page_config(
    page_title="ETS Real-Time Analytics",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #888;
        margin-bottom: 2rem;
    }
    .last-updated {
        text-align: center;
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🚌 Edmonton Transit System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Real-Time Performance Analytics Dashboard</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("⚙️ Dashboard Controls")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=True)
    
    # Manual refresh button
    if st.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()
    
    # Filters
    st.subheader("Filters")
    
    # Route filter placeholder (will be populated with actual routes)
    selected_routes = st.multiselect(
        "Select Routes",
        options=[],
        default=[],
        help="Filter data by specific routes"
    )
    
    # Time range filter
    time_range = st.selectbox(
        "Time Range",
        options=["Last Hour", "Last 4 Hours", "Last 12 Hours", "Last 24 Hours", "All Time"],
        index=3
    )
    
    st.divider()
    
    # About section
    st.subheader("📊 About")
    st.markdown("""
    This dashboard provides real-time insights into Edmonton Transit System performance:
    
    - **Live Vehicle Tracking**: See bus positions in real-time
    - **Delay Analytics**: Identify delay patterns by route and time
    - **Performance Metrics**: Track on-time performance
    - **ML Predictions**: AI-powered delay forecasting
    """)
    
    st.divider()
    
    # Data source info
    st.caption("Data Source: Edmonton Open Data Portal")
    st.caption("Update Frequency: Every 30 seconds")
    st.caption("Built with Streamlit | AWS | Python")

# Load data (without spinner to avoid screen darkening)
data = load_dashboard_data()
vehicles_df = data['vehicles']
trip_updates_df = data['trip_updates']
data_source = data.get('data_source', 'live')

# Show banner when using mock data (e.g. Streamlit Cloud without Secrets)
if data_source == 'mock':
    st.warning(
        "**Using sample data.** To see live Edmonton Transit data, add AWS credentials in Streamlit Cloud: "
        "app **Settings** → **Secrets** → paste your `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, "
        "`AWS_REGION` (us-east-2), and `DYNAMODB_TABLE_NAME` (ets_transit_processed)."
    )

# Last refreshed timestamp with countdown
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f'<div class="last-updated">Last Refreshed: {current_time} • Auto-refresh in 30s</div>', unsafe_allow_html=True)

# Apply filters
if selected_routes:
    if not vehicles_df.empty:
        vehicles_df = vehicles_df[vehicles_df['route_id'].isin(selected_routes)]
    if not trip_updates_df.empty:
        trip_updates_df = trip_updates_df[trip_updates_df['route_id'].isin(selected_routes)]

# KPI Cards
render_kpi_cards(vehicles_df, trip_updates_df)

st.divider()

# Main content area - two columns
col1, col2 = st.columns([2, 1])

with col1:
    # Live Map
    render_live_map(vehicles_df, trip_updates_df)

with col2:
    # Route Performance
    render_route_performance(trip_updates_df, top_n=10)

st.divider()

# Delay Heatmap (full width)
render_delay_heatmap(trip_updates_df)

st.divider()

# Additional insights
with st.expander("📈 Additional Analytics"):
    tab1, tab2, tab3 = st.tabs(["Delay Distribution", "Hourly Trends", "Raw Data"])
    
    with tab1:
        if not trip_updates_df.empty and 'delay_minutes' in trip_updates_df.columns:
            st.subheader("Delay Distribution")
            import plotly.express as px
            
            fig = px.histogram(
                trip_updates_df,
                x='delay_minutes',
                nbins=50,
                title="Distribution of Delays",
                labels={'delay_minutes': 'Delay (minutes)', 'count': 'Frequency'}
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No delay data available")
    
    with tab2:
        if not trip_updates_df.empty and 'delay_minutes' in trip_updates_df.columns:
            st.subheader("Hourly Delay Trends")
            
            # Extract hour if not present
            if 'hour' not in trip_updates_df.columns:
                trip_updates_df['hour'] = pd.to_datetime(trip_updates_df['feed_timestamp']).dt.hour
            
            hourly_avg = trip_updates_df.groupby('hour')['delay_minutes'].mean().reset_index()
            
            import plotly.express as px
            fig = px.line(
                hourly_avg,
                x='hour',
                y='delay_minutes',
                title="Average Delay by Hour of Day",
                labels={'hour': 'Hour of Day', 'delay_minutes': 'Avg Delay (min)'},
                markers=True
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No delay data available")
    
    with tab3:
        st.subheader("Raw Data Preview")
        
        data_choice = st.radio("Select data type:", ["Vehicle Positions", "Trip Updates"])
        
        if data_choice == "Vehicle Positions":
            if not vehicles_df.empty:
                st.dataframe(vehicles_df.head(100), width='stretch')
                st.caption(f"Showing first 100 of {len(vehicles_df)} records")
            else:
                st.info("No vehicle data available")
        else:
            if not trip_updates_df.empty:
                st.dataframe(trip_updates_df.head(100), width='stretch')
                st.caption(f"Showing first 100 of {len(trip_updates_df)} records")
            else:
                st.info("No trip update data available")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>Edmonton Transit System Real-Time Analytics Dashboard</p>
    <p>Data Engineering | Machine Learning | Data Visualization</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh logic
if auto_refresh:
    time.sleep(30)
    st.rerun()
