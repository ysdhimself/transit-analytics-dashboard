"""
Route performance bar chart component for dashboard.
Shows average delay per route, sorted descending.
"""
import streamlit as st
import pandas as pd
import plotly.express as px


def render_route_performance(trip_updates_df: pd.DataFrame, top_n: int = 15):
    """
    Render route performance bar chart.
    
    Args:
        trip_updates_df: DataFrame with trip updates and delays
        top_n: Number of routes to display
    """
    st.subheader("📊 Route Performance Ranking")
    
    if trip_updates_df.empty or 'delay_minutes' not in trip_updates_df.columns:
        st.info("No delay data available to display route performance")
        return
    
    # Get route identifier
    if 'route_short_name' in trip_updates_df.columns:
        route_col = 'route_short_name'
        route_name_col = 'route_long_name' if 'route_long_name' in trip_updates_df.columns else 'route_short_name'
    else:
        route_col = 'route_id'
        route_name_col = 'route_id'
    
    # Calculate statistics by route
    route_stats = trip_updates_df.groupby(route_col).agg({
        'delay_minutes': ['mean', 'count'],
        route_name_col: 'first'
    }).reset_index()
    
    # Flatten column names
    route_stats.columns = [route_col, 'avg_delay', 'num_updates', 'route_name']
    
    # Filter routes with sufficient data (at least 5 updates)
    route_stats = route_stats[route_stats['num_updates'] >= 5]
    
    # Sort by average delay descending and take top N
    route_stats = route_stats.sort_values('avg_delay', ascending=False).head(top_n)
    
    if route_stats.empty:
        st.info("Insufficient data for route performance analysis")
        return
    
    # Create bar chart
    fig = px.bar(
        route_stats,
        x='avg_delay',
        y=route_col,
        orientation='h',
        color='avg_delay',
        color_continuous_scale='RdYlGn_r',  # Red for high delays
        labels={'avg_delay': 'Average Delay (min)', route_col: 'Route'},
        hover_data={'num_updates': True, 'route_name': True},
        title=f"Top {len(route_stats)} Routes by Average Delay"
    )
    
    fig.update_layout(
        height=max(400, len(route_stats) * 30),
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'}  # Sort bars by value
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display data table
    with st.expander("📋 View Route Performance Data"):
        display_df = route_stats.copy()
        display_df['avg_delay'] = display_df['avg_delay'].apply(lambda x: f"{x:.2f} min")
        display_df = display_df.rename(columns={
            route_col: 'Route',
            'avg_delay': 'Avg Delay',
            'num_updates': 'Sample Size',
            'route_name': 'Route Name'
        })
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
