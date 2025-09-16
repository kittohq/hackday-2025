import math
import logging
from typing import Dict, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LocationService:
    def __init__(self):
        self.earth_radius_miles = 3959.0

    def calculate_distance(
        self,
        point1: Dict[str, float],
        point2: Dict[str, float]
    ) -> float:
        """
        Calculate distance between two points using Haversine formula
        Returns distance in miles
        """
        lat1 = math.radians(point1["lat"])
        lon1 = math.radians(point1["lng"])
        lat2 = math.radians(point2["lat"])
        lon2 = math.radians(point2["lng"])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        return self.earth_radius_miles * c

    def calculate_detour_time(
        self,
        current_location: Dict[str, float],
        destination: Dict[str, float],
        final_destination: Dict[str, float],
        average_speed_mph: float = 30.0
    ) -> int:
        """
        Calculate additional time in minutes for a detour
        """
        direct_distance = self.calculate_distance(current_location, final_destination)

        detour_distance = (
            self.calculate_distance(current_location, destination) +
            self.calculate_distance(destination, final_destination)
        )

        extra_distance = detour_distance - direct_distance

        extra_time_minutes = int((extra_distance / average_speed_mph) * 60)

        extra_time_minutes += 5

        return max(extra_time_minutes, 2)

    def estimate_arrival_time(
        self,
        current_location: Dict[str, float],
        destination: Dict[str, float],
        traffic_factor: float = 1.0
    ) -> Tuple[int, str]:
        """
        Estimate arrival time based on current location and traffic
        Returns (minutes, formatted_time)
        """
        distance = self.calculate_distance(current_location, destination)

        base_speed = 35.0
        adjusted_speed = base_speed / traffic_factor

        travel_time_minutes = int((distance / adjusted_speed) * 60)

        arrival_time = datetime.now()
        arrival_time = arrival_time.replace(
            hour=(arrival_time.hour + travel_time_minutes // 60) % 24,
            minute=(arrival_time.minute + travel_time_minutes % 60) % 60
        )

        formatted_time = arrival_time.strftime("%I:%M %p")

        return travel_time_minutes, formatted_time

    def get_traffic_condition(self, traffic_factor: float) -> str:
        """Convert traffic factor to human-readable condition"""
        if traffic_factor < 1.2:
            return "light"
        elif traffic_factor < 1.5:
            return "moderate"
        elif traffic_factor < 2.0:
            return "heavy"
        else:
            return "severe"

    def find_optimal_route(
        self,
        current_location: Dict[str, float],
        destination: Dict[str, float],
        avoid_highways: bool = False,
        prefer_scenic: bool = False
    ) -> Dict[str, any]:
        """
        Find optimal route based on preferences
        This is a simplified version - real implementation would use mapping APIs
        """

        routes = []

        routes.append({
            "name": "Fastest Route via US-101",
            "distance_miles": self.calculate_distance(current_location, destination),
            "estimated_minutes": 25,
            "type": "highway",
            "description": "Take US-101 North for fastest arrival"
        })

        routes.append({
            "name": "Scenic Coastal Route",
            "distance_miles": self.calculate_distance(current_location, destination) * 1.3,
            "estimated_minutes": 35,
            "type": "scenic",
            "description": "Take Highway 1 for beautiful ocean views"
        })

        routes.append({
            "name": "City Streets",
            "distance_miles": self.calculate_distance(current_location, destination) * 1.1,
            "estimated_minutes": 30,
            "type": "local",
            "description": "Take local streets through neighborhoods"
        })

        if avoid_highways:
            routes = [r for r in routes if r["type"] != "highway"]

        if prefer_scenic:
            routes.sort(key=lambda x: 0 if x["type"] == "scenic" else 1)
        else:
            routes.sort(key=lambda x: x["estimated_minutes"])

        return routes[0] if routes else {
            "name": "Direct Route",
            "distance_miles": self.calculate_distance(current_location, destination),
            "estimated_minutes": 25,
            "type": "standard",
            "description": "Standard route to destination"
        }

    def get_nearby_categories(self, location_type: str) -> Dict[str, str]:
        """Map location types to Yelp categories"""
        category_map = {
            "coffee": "coffee,coffeeroasteries",
            "food": "restaurants",
            "gas": "servicestations",
            "pharmacy": "pharmacy",
            "grocery": "grocery",
            "bank": "banks",
            "atm": "banks",
            "hotel": "hotels",
            "parking": "parking"
        }

        return category_map.get(location_type.lower(), "restaurants")