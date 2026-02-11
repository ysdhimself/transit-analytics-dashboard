"""
Delay calculator for GTFS-RT data.
Computes delay_minutes by comparing real-time arrival times with scheduled times.
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict


class DelayCalculator:
    """Calculator for transit delays using GTFS-RT and static schedule data."""
    
    def __init__(self, static_schedule: pd.DataFrame):
        """
        Initialize the delay calculator.
        
        Args:
            static_schedule: DataFrame with static GTFS schedule data
        """
        self.static_schedule = static_schedule
        
        # Convert arrival_time and departure_time to seconds for comparison
        if 'arrival_time' in static_schedule.columns:
            self.static_schedule['arrival_seconds'] = self.static_schedule['arrival_time'].apply(
                self._time_to_seconds
            )
    
    def _time_to_seconds(self, time_str: str) -> int:
        """
        Convert HH:MM:SS time string to seconds since midnight.
        GTFS allows times > 24:00:00 for trips after midnight.
        
        Args:
            time_str: Time string in HH:MM:SS format
            
        Returns:
            Seconds since midnight (can be > 86400)
        """
        if pd.isna(time_str):
            return 0
        
        try:
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        except:
            return 0
    
    def calculate_delay_from_trip_updates(self, trip_updates: List[Dict]) -> pd.DataFrame:
        """
        Calculate delays directly from GTFS-RT Trip Updates.
        Trip Updates contain arrival_delay field (in seconds).
        
        Args:
            trip_updates: List of trip update records
            
        Returns:
            DataFrame with delay information
        """
        if not trip_updates:
            return pd.DataFrame()
        
        df = pd.DataFrame(trip_updates)
        
        # Convert arrival_delay (seconds) to delay_minutes
        df['delay_minutes'] = df['arrival_delay'] / 60.0
        
        # Fill missing values with 0
        df['delay_minutes'] = df['delay_minutes'].fillna(0)
        
        # Add timestamp for analysis
        df['feed_timestamp'] = pd.to_datetime(df['feed_timestamp'])
        
        return df
    
    def merge_realtime_with_schedule(
        self,
        trip_updates: pd.DataFrame,
        include_schedule_info: bool = True
    ) -> pd.DataFrame:
        """
        Merge real-time trip updates with static schedule information.
        
        Args:
            trip_updates: DataFrame with trip update records
            include_schedule_info: If True, include stop names, route info, etc.
            
        Returns:
            Merged DataFrame with delay and schedule information
        """
        if trip_updates.empty:
            return pd.DataFrame()
        
        if not include_schedule_info:
            return trip_updates
        
        # Merge with static schedule on trip_id and stop_id
        merged = trip_updates.merge(
            self.static_schedule[[
                'trip_id', 'stop_id', 'stop_sequence', 'arrival_time',
                'route_id', 'route_short_name', 'route_long_name',
                'stop_name', 'stop_lat', 'stop_lon'
            ]].drop_duplicates(subset=['trip_id', 'stop_id']),
            on=['trip_id', 'stop_id'],
            how='left',
            suffixes=('', '_scheduled')
        )
        
        return merged
    
    def calculate_delay_statistics(self, delays_df: pd.DataFrame) -> Dict:
        """
        Calculate summary statistics for delays.
        
        Args:
            delays_df: DataFrame with delay_minutes column
            
        Returns:
            Dictionary with delay statistics
        """
        if delays_df.empty or 'delay_minutes' not in delays_df.columns:
            return {
                'total_records': 0,
                'avg_delay_minutes': 0,
                'median_delay_minutes': 0,
                'max_delay_minutes': 0,
                'min_delay_minutes': 0,
                'on_time_rate': 0
            }
        
        # Calculate on-time rate (within 5 minutes of schedule)
        on_time_count = len(delays_df[delays_df['delay_minutes'].abs() <= 5])
        on_time_rate = on_time_count / len(delays_df) if len(delays_df) > 0 else 0
        
        return {
            'total_records': len(delays_df),
            'avg_delay_minutes': float(delays_df['delay_minutes'].mean()),
            'median_delay_minutes': float(delays_df['delay_minutes'].median()),
            'max_delay_minutes': float(delays_df['delay_minutes'].max()),
            'min_delay_minutes': float(delays_df['delay_minutes'].min()),
            'on_time_rate': float(on_time_rate),
            'std_delay_minutes': float(delays_df['delay_minutes'].std())
        }
    
    def calculate_delay_by_route(self, delays_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate average delay by route.
        
        Args:
            delays_df: DataFrame with delay_minutes and route_id columns
            
        Returns:
            DataFrame with route-level statistics
        """
        if delays_df.empty or 'delay_minutes' not in delays_df.columns:
            return pd.DataFrame()
        
        route_stats = delays_df.groupby('route_id').agg({
            'delay_minutes': ['mean', 'median', 'std', 'count'],
            'route_short_name': 'first',
            'route_long_name': 'first'
        }).reset_index()
        
        # Flatten column names
        route_stats.columns = [
            'route_id', 'avg_delay', 'median_delay', 'std_delay', 'count',
            'route_short_name', 'route_long_name'
        ]
        
        # Calculate on-time rate per route
        def calc_on_time_rate(group):
            return (group['delay_minutes'].abs() <= 5).sum() / len(group)
        
        on_time_rates = delays_df.groupby('route_id').apply(calc_on_time_rate).reset_index()
        on_time_rates.columns = ['route_id', 'on_time_rate']
        
        route_stats = route_stats.merge(on_time_rates, on='route_id')
        
        # Sort by average delay descending
        route_stats = route_stats.sort_values('avg_delay', ascending=False)
        
        return route_stats
    
    def calculate_delay_by_hour(self, delays_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate average delay by hour of day.
        
        Args:
            delays_df: DataFrame with delay_minutes and timestamp columns
            
        Returns:
            DataFrame with hourly statistics
        """
        if delays_df.empty or 'delay_minutes' not in delays_df.columns:
            return pd.DataFrame()
        
        # Extract hour from feed_timestamp
        delays_df['hour'] = pd.to_datetime(delays_df['feed_timestamp']).dt.hour
        
        hourly_stats = delays_df.groupby('hour').agg({
            'delay_minutes': ['mean', 'median', 'count']
        }).reset_index()
        
        # Flatten column names
        hourly_stats.columns = ['hour', 'avg_delay', 'median_delay', 'count']
        
        return hourly_stats


# Convenience functions
def calculate_delays(trip_updates: List[Dict], static_schedule: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate delays from trip updates and merge with schedule.
    
    Args:
        trip_updates: List of trip update records
        static_schedule: Static GTFS schedule DataFrame
        
    Returns:
        DataFrame with delay information
    """
    calculator = DelayCalculator(static_schedule)
    delays_df = calculator.calculate_delay_from_trip_updates(trip_updates)
    return calculator.merge_realtime_with_schedule(delays_df)


if __name__ == '__main__':
    # Test delay calculator
    print("Testing Delay Calculator...")
    
    # Sample test data
    test_trip_updates = [
        {
            'trip_id': 'trip1',
            'route_id': 'route1',
            'stop_id': 'stop1',
            'arrival_delay': 120,  # 2 minutes late
            'feed_timestamp': '2024-01-01T10:00:00'
        },
        {
            'trip_id': 'trip1',
            'route_id': 'route1',
            'stop_id': 'stop2',
            'arrival_delay': 300,  # 5 minutes late
            'feed_timestamp': '2024-01-01T10:05:00'
        }
    ]
    
    # Create minimal static schedule
    test_schedule = pd.DataFrame({
        'trip_id': ['trip1', 'trip1'],
        'stop_id': ['stop1', 'stop2'],
        'stop_sequence': [1, 2],
        'arrival_time': ['10:00:00', '10:05:00'],
        'route_id': ['route1', 'route1'],
        'route_short_name': ['1', '1'],
        'route_long_name': ['Route 1', 'Route 1'],
        'stop_name': ['Stop 1', 'Stop 2'],
        'stop_lat': [53.5, 53.6],
        'stop_lon': [-113.5, -113.6]
    })
    
    calculator = DelayCalculator(test_schedule)
    delays = calculator.calculate_delay_from_trip_updates(test_trip_updates)
    
    print(f"\nDelays calculated: {len(delays)} records")
    print(delays[['trip_id', 'stop_id', 'arrival_delay', 'delay_minutes']])
    
    stats = calculator.calculate_delay_statistics(delays)
    print(f"\nStatistics: {stats}")
