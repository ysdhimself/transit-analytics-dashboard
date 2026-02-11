"""
KPI cards component for dashboard.
Displays Active Buses, Average Delay, and On-Time Rate.
"""
import streamlit as st
import pandas as pd


def render_kpi_cards(vehicles_df: pd.DataFrame, trip_updates_df: pd.DataFrame):
    """
    Render KPI metric cards.
    
    Args:
        vehicles_df: DataFrame with vehicle positions
        trip_updates_df: DataFrame with trip updates and delays
    """
    col1, col2, col3 = st.columns(3)
    
    # KPI 1: Active Buses
    with col1:
        active_buses = len(vehicles_df['vehicle_id'].unique()) if not vehicles_df.empty else 0
        st.metric(
            label="🚌 Active Buses",
            value=active_buses,
            help="Number of buses currently transmitting position data"
        )
    
    # KPI 2: Average Delay
    with col2:
        if not trip_updates_df.empty and 'delay_minutes' in trip_updates_df.columns:
            avg_delay = trip_updates_df['delay_minutes'].mean()
            
            # Determine delta color (negative is good for delays)
            delta_color = "normal" if avg_delay <= 3 else "inverse"
            
            st.metric(
                label="⏱️ Average Delay",
                value=f"{avg_delay:.1f} min",
                delta=f"{abs(avg_delay):.1f} min",
                delta_color=delta_color,
                help="Average delay across all routes and stops"
            )
        else:
            st.metric(
                label="⏱️ Average Delay",
                value="N/A",
                help="No delay data available"
            )
    
    # KPI 3: On-Time Rate
    with col3:
        if not trip_updates_df.empty and 'delay_minutes' in trip_updates_df.columns:
            # On-time = within 5 minutes of schedule
            on_time_count = (trip_updates_df['delay_minutes'].abs() <= 5).sum()
            total_count = len(trip_updates_df)
            on_time_rate = (on_time_count / total_count * 100) if total_count > 0 else 0
            
            # Determine delta (higher is better)
            delta_text = "Good" if on_time_rate >= 80 else "Below Target"
            delta_color = "normal" if on_time_rate >= 80 else "inverse"
            
            st.metric(
                label="✅ On-Time Rate",
                value=f"{on_time_rate:.1f}%",
                delta=delta_text,
                delta_color=delta_color,
                help="Percentage of trips within 5 minutes of schedule"
            )
        else:
            st.metric(
                label="✅ On-Time Rate",
                value="N/A",
                help="No delay data available"
            )
