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
    
    # Add color based on delay
    if 'delay_minutes' in vehicles_df.columns:
        def get_color(delay):
            if pd.isna(delay):
                return [128, 128, 128, 200]  # Gray for unknown
            elif delay <= 2:
                return [0, 200, 0, 200]  # Green for on-time
            elif delay <= 5:
                return [255, 255, 0, 200]  # Yellow for slight delay
            else:
                return [255, 0, 0, 200]  # Red for significant delay
        
        vehicles_df['color'] = vehicles_df['delay_minutes'].apply(get_color)
    else:
        # Default blue if no delay data
        vehicles_df['color'] = [[0, 100, 255, 200]] * len(vehicles_df)
    
    # Calculate map center
    center_lat = vehicles_df['latitude'].mean()
    center_lon = vehicles_df['longitude'].mean()
    
    # Create PyDeck layer
    layer = pdk.Layer(
        'ScatterplotLayer',
        data=vehicles_df,
        get_position='[longitude, latitude]',
        get_color='color',
        get_radius=100,
        pickable=True,
        auto_highlight=True
    )
    
    # Set view state
    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=11,
        pitch=0
    )
    
    # Create deck
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={
            'html': '<b>Vehicle:</b> {vehicle_id}<br/>'
                   '<b>Route:</b> {route_id}<br/>'
                   '<b>Speed:</b> {speed} km/h<br/>'
                   '<b>Delay:</b> {delay_minutes} min',
            'style': {
                'backgroundColor': 'steelblue',
                'color': 'white'
            }
        }
    )
    
    st.pydeck_chart(deck)
    
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
