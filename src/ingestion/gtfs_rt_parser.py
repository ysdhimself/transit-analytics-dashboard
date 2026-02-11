"""
GTFS Real-Time protobuf parser for Edmonton Transit System.
Parses Vehicle Positions and Trip Updates feeds.
"""
import requests
import os
from datetime import datetime
from typing import List, Dict, Optional
from google.transit import gtfs_realtime_pb2

# Get config from environment variables (Lambda)
GTFS_RT_VEHICLE_POSITIONS_URL = os.getenv(
    'GTFS_RT_VEHICLE_POSITIONS_URL',
    'https://gtfs.edmonton.ca/TMGTFSRealTimeWebService/Vehicle/VehiclePositions.pb'
)
GTFS_RT_TRIP_UPDATES_URL = os.getenv(
    'GTFS_RT_TRIP_UPDATES_URL',
    'https://gtfs.edmonton.ca/TMGTFSRealTimeWebService/TripUpdate/TripUpdates.pb'
)


class GTFSRealtimeParser:
    """Parser for GTFS-RT protobuf feeds."""
    
    def __init__(self):
        """Initialize the parser."""
        self.vehicle_positions_url = GTFS_RT_VEHICLE_POSITIONS_URL
        self.trip_updates_url = GTFS_RT_TRIP_UPDATES_URL
    
    def fetch_protobuf_feed(self, url: str) -> Optional[gtfs_realtime_pb2.FeedMessage]:
        """
        Fetch and parse a GTFS-RT protobuf feed.
        
        Args:
            url: URL of the protobuf feed
            
        Returns:
            Parsed FeedMessage or None if fetch fails
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)
            
            return feed
        except Exception as e:
            print(f"Error fetching protobuf feed from {url}: {e}")
            return None
    
    def parse_vehicle_positions(self) -> List[Dict]:
        """
        Parse Vehicle Positions feed into structured records.
        
        Returns:
            List of dictionaries with vehicle position data
        """
        feed = self.fetch_protobuf_feed(self.vehicle_positions_url)
        if not feed:
            return []
        
        vehicles = []
        
        for entity in feed.entity:
            if entity.HasField('vehicle'):
                vehicle = entity.vehicle
                
                record = {
                    'vehicle_id': vehicle.vehicle.id if vehicle.HasField('vehicle') else None,
                    'trip_id': vehicle.trip.trip_id if vehicle.HasField('trip') else None,
                    'route_id': vehicle.trip.route_id if vehicle.HasField('trip') else None,
                    'latitude': vehicle.position.latitude if vehicle.HasField('position') else None,
                    'longitude': vehicle.position.longitude if vehicle.HasField('position') else None,
                    'bearing': vehicle.position.bearing if vehicle.HasField('position') and vehicle.position.HasField('bearing') else None,
                    'speed': vehicle.position.speed if vehicle.HasField('position') and vehicle.position.HasField('speed') else None,
                    'timestamp': datetime.fromtimestamp(vehicle.timestamp).isoformat() if vehicle.HasField('timestamp') else datetime.now().isoformat(),
                    'current_stop_sequence': vehicle.current_stop_sequence if vehicle.HasField('current_stop_sequence') else None,
                    'current_status': vehicle.current_status if vehicle.HasField('current_status') else None,
                    'congestion_level': vehicle.congestion_level if vehicle.HasField('congestion_level') else None,
                    'feed_timestamp': datetime.fromtimestamp(feed.header.timestamp).isoformat() if feed.header.HasField('timestamp') else datetime.now().isoformat()
                }
                
                vehicles.append(record)
        
        print(f"Parsed {len(vehicles)} vehicle positions")
        return vehicles
    
    def parse_trip_updates(self) -> List[Dict]:
        """
        Parse Trip Updates feed into structured records.
        
        Returns:
            List of dictionaries with trip update data (delays at each stop)
        """
        feed = self.fetch_protobuf_feed(self.trip_updates_url)
        if not feed:
            return []
        
        updates = []
        
        for entity in feed.entity:
            if entity.HasField('trip_update'):
                trip_update = entity.trip_update
                
                trip_id = trip_update.trip.trip_id if trip_update.HasField('trip') else None
                route_id = trip_update.trip.route_id if trip_update.HasField('trip') else None
                vehicle_id = trip_update.vehicle.id if trip_update.HasField('vehicle') else None
                
                # Each trip update has multiple stop_time_updates
                for stop_time_update in trip_update.stop_time_update:
                    record = {
                        'trip_id': trip_id,
                        'route_id': route_id,
                        'vehicle_id': vehicle_id,
                        'stop_id': stop_time_update.stop_id if stop_time_update.HasField('stop_id') else None,
                        'stop_sequence': stop_time_update.stop_sequence if stop_time_update.HasField('stop_sequence') else None,
                        'arrival_delay': stop_time_update.arrival.delay if stop_time_update.HasField('arrival') and stop_time_update.arrival.HasField('delay') else None,
                        'arrival_time': datetime.fromtimestamp(stop_time_update.arrival.time).isoformat() if stop_time_update.HasField('arrival') and stop_time_update.arrival.HasField('time') else None,
                        'departure_delay': stop_time_update.departure.delay if stop_time_update.HasField('departure') and stop_time_update.departure.HasField('delay') else None,
                        'departure_time': datetime.fromtimestamp(stop_time_update.departure.time).isoformat() if stop_time_update.HasField('departure') and stop_time_update.departure.HasField('time') else None,
                        'schedule_relationship': stop_time_update.schedule_relationship if stop_time_update.HasField('schedule_relationship') else None,
                        'feed_timestamp': datetime.fromtimestamp(feed.header.timestamp).isoformat() if feed.header.HasField('timestamp') else datetime.now().isoformat()
                    }
                    
                    updates.append(record)
        
        print(f"Parsed {len(updates)} trip updates")
        return updates
    
    def parse_all(self) -> Dict[str, List[Dict]]:
        """
        Parse both Vehicle Positions and Trip Updates.
        
        Returns:
            Dictionary with 'vehicles' and 'trip_updates' keys
        """
        return {
            'vehicles': self.parse_vehicle_positions(),
            'trip_updates': self.parse_trip_updates()
        }


# Convenience functions
def get_vehicle_positions() -> List[Dict]:
    """Fetch and parse current vehicle positions."""
    parser = GTFSRealtimeParser()
    return parser.parse_vehicle_positions()


def get_trip_updates() -> List[Dict]:
    """Fetch and parse current trip updates (delays)."""
    parser = GTFSRealtimeParser()
    return parser.parse_trip_updates()


def get_all_realtime_data() -> Dict[str, List[Dict]]:
    """Fetch and parse all real-time data."""
    parser = GTFSRealtimeParser()
    return parser.parse_all()


if __name__ == '__main__':
    # Test the parser
    print("Testing GTFS-RT Parser...")
    data = get_all_realtime_data()
    
    print(f"\nVehicle Positions: {len(data['vehicles'])} records")
    if data['vehicles']:
        print("Sample vehicle:", data['vehicles'][0])
    
    print(f"\nTrip Updates: {len(data['trip_updates'])} records")
    if data['trip_updates']:
        print("Sample trip update:", data['trip_updates'][0])
