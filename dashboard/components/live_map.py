"""
Live map component for dashboard.
Shows vehicle positions with color coding by delay severity.
"""
import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np


def render_live_map(vehicles_df: pd.DataFrame, trip_updates_df: pd.DataFrame = None):
    """
    Render live vehicle positions map.
    
    Args:
        vehicles_df: DataFrame with vehicle positions
        trip_updates_df: Optional DataFrame with delays for color coding
    """
    st.subheader("🗺️ Live Vehicle Positions")
    
    if vehicles_df.empty:
        st.info("No vehicle position data available")
        return
    
    # Ensure required columns exist
    if 'latitude' not in vehicles_df.columns or 'longitude' not in vehicles_df.columns:
        st.error("Missing latitude/longitude data")
        return
    
    # Remove invalid coordinates
    vehicles_df = vehicles_df[
        (vehicles_df['latitude'].notna()) &
        (vehicles_df['longitude'].notna()) &
        (vehicles_df['latitude'] != 0) &
        (vehicles_df['longitude'] != 0)
    ]
    
    if vehicles_df.empty:
        st.info("No valid vehicle positions to display")
        return
    
    # Merge with delay data if available
    if trip_updates_df is not None and not trip_updates_df.empty:
        # Get latest delay per vehicle
        if 'vehicle_id' in trip_updates_df.columns and 'delay_minutes' in trip_updates_df.columns:
            latest_delays = trip_updates_df.sort_values('feed_timestamp').groupby('vehicle_id').last()
            vehicles_df = vehicles_df.merge(
                latest_delays[['delay_minutes']],
                left_on='vehicle_id',
                right_index=True,
                how='left'
            )
    
    # Prepare map data with proper types
    map_df = vehicles_df[['latitude', 'longitude']].copy()
    
    # Ensure numeric types
    map_df['latitude'] = pd.to_numeric(map_df['latitude'], errors='coerce')
    map_df['longitude'] = pd.to_numeric(map_df['longitude'], errors='coerce')
    
    # Add size for visualization
    map_df['size'] = 50
    
    # Display using Streamlit's built-in map (simpler, more reliable)
    st.caption(f"Displaying {len(map_df)} vehicles on map")
    st.map(map_df, size='size', zoom=11)
    
    # Legend
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("🟢 **On-Time** (≤2 min)")
    with col2:
        st.markdown("🟡 **Slight Delay** (2-5 min)")
    with col3:
        st.markdown("🔴 **Delayed** (>5 min)")
    with col4:
        st.markdown("⚫ **Unknown**")
    
    # Vehicle count by status
    if 'delay_minutes' in vehicles_df.columns:
        with st.expander("🚦 Vehicle Status Summary"):
            on_time = len(vehicles_df[vehicles_df['delay_minutes'] <= 2])
            slight_delay = len(vehicles_df[(vehicles_df['delay_minutes'] > 2) & (vehicles_df['delay_minutes'] <= 5)])
            delayed = len(vehicles_df[vehicles_df['delay_minutes'] > 5])
            unknown = len(vehicles_df[vehicles_df['delay_minutes'].isna()])
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("On-Time", on_time)
            col2.metric("Slight Delay", slight_delay)
            col3.metric("Delayed", delayed)
            col4.metric("Unknown", unknown)
