"""
Delay heatmap component for dashboard.
Shows density heatmap of delays by route and hour.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def render_delay_heatmap(trip_updates_df: pd.DataFrame):
    """
    Render delay heatmap showing route vs hour.
    
    Args:
        trip_updates_df: DataFrame with trip updates and delays
    """
    st.subheader("🔥 Delay Heatmap: Route vs Hour")
    
    if trip_updates_df.empty or 'delay_minutes' not in trip_updates_df.columns:
        st.info("No delay data available to display heatmap")
        return
    
    # Extract hour if not already present
    if 'hour' not in trip_updates_df.columns:
        trip_updates_df['hour'] = pd.to_datetime(trip_updates_df['feed_timestamp']).dt.hour
    
    # Get route name for display
    if 'route_short_name' in trip_updates_df.columns:
        route_col = 'route_short_name'
    else:
        route_col = 'route_id'
    
    # Calculate average delay by route and hour
    heatmap_data = trip_updates_df.groupby([route_col, 'hour'])['delay_minutes'].mean().reset_index()
    
    # Pivot for heatmap format
    heatmap_pivot = heatmap_data.pivot(index=route_col, columns='hour', values='delay_minutes')
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_pivot.values,
        x=heatmap_pivot.columns,
        y=heatmap_pivot.index,
        colorscale='RdYlGn_r',  # Red for high delays, green for low
        colorbar=dict(title="Delay (min)"),
        hovertemplate='Route: %{y}<br>Hour: %{x}:00<br>Avg Delay: %{z:.2f} min<extra></extra>'
    ))
    
    fig.update_layout(
        title="Average Delay by Route and Hour of Day",
        xaxis_title="Hour of Day",
        yaxis_title="Route",
        height=400,
        xaxis=dict(dtick=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary insights
    with st.expander("📊 Heatmap Insights"):
        # Most delayed hour
        most_delayed_hour = heatmap_data.groupby('hour')['delay_minutes'].mean().idxmax()
        avg_delay_at_peak = heatmap_data.groupby('hour')['delay_minutes'].mean().max()
        
        # Most delayed route
        most_delayed_route = heatmap_data.groupby(route_col)['delay_minutes'].mean().idxmax()
        route_avg_delay = heatmap_data.groupby(route_col)['delay_minutes'].mean().max()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Peak Delay Hour",
                f"{most_delayed_hour}:00",
                f"{avg_delay_at_peak:.1f} min avg"
            )
        
        with col2:
            st.metric(
                "Most Delayed Route",
                f"Route {most_delayed_route}",
                f"{route_avg_delay:.1f} min avg"
            )
