import os
import httpx
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class YelpService:
    def __init__(self):
        self.api_key = os.getenv("YELP_API_KEY")
        self.base_url = "https://api.yelp.com/v3"
        self.client = httpx.AsyncClient()
        self._mock_mode = not bool(self.api_key)

        if self._mock_mode:
            logger.warning("Yelp API key not found - using mock data")

    async def search_nearby(
        self,
        latitude: float,
        longitude: float,
        term: str = "",
        radius: int = 5000,
        limit: int = 5,
        categories: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for businesses near a location
        """
        if self._mock_mode:
            return self._get_mock_results(term, latitude, longitude)

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }

            params = {
                "latitude": latitude,
                "longitude": longitude,
                "term": term,
                "radius": min(radius, 40000),
                "limit": limit,
                "sort_by": "distance"
            }

            if categories:
                params["categories"] = categories

            response = await self.client.get(
                f"{self.base_url}/businesses/search",
                headers=headers,
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                return self._format_results(data.get("businesses", []))
            else:
                logger.error(f"Yelp API error: {response.status_code}")
                return self._get_mock_results(term, latitude, longitude)

        except Exception as e:
            logger.error(f"Error searching Yelp: {str(e)}")
            return self._get_mock_results(term, latitude, longitude)

    async def get_business_details(self, business_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific business"""
        if self._mock_mode:
            return self._get_mock_business_details()

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }

            response = await self.client.get(
                f"{self.base_url}/businesses/{business_id}",
                headers=headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except Exception as e:
            logger.error(f"Error getting business details: {str(e)}")
            return None

    def _format_results(self, businesses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format Yelp API results for our use"""
        formatted = []

        for business in businesses:
            formatted.append({
                "id": business.get("id"),
                "name": business.get("name"),
                "rating": business.get("rating"),
                "review_count": business.get("review_count"),
                "price": business.get("price", ""),
                "distance": business.get("distance"),
                "categories": [cat["title"] for cat in business.get("categories", [])],
                "address": business.get("location", {}).get("display_address", []),
                "phone": business.get("phone"),
                "coordinates": business.get("coordinates", {}),
                "is_closed": business.get("is_closed", False)
            })

        return formatted

    def _get_mock_results(self, term: str, latitude: float, longitude: float) -> List[Dict[str, Any]]:
        """Return mock data for testing"""
        mock_data = {
            "coffee": [
                {
                    "id": "blue-bottle-coffee-sf",
                    "name": "Blue Bottle Coffee",
                    "rating": 4.5,
                    "review_count": 1523,
                    "price": "$$",
                    "distance": 523.5,
                    "categories": ["Coffee & Tea"],
                    "address": ["300 Webster St", "San Francisco, CA 94117"],
                    "phone": "+14156531394",
                    "coordinates": {"latitude": latitude + 0.005, "longitude": longitude + 0.003},
                    "is_closed": False
                },
                {
                    "id": "ritual-coffee-sf",
                    "name": "Ritual Coffee Roasters",
                    "rating": 4.3,
                    "review_count": 892,
                    "price": "$$",
                    "distance": 812.3,
                    "categories": ["Coffee & Tea"],
                    "address": ["432 Octavia St", "San Francisco, CA 94102"],
                    "phone": "+14158651405",
                    "coordinates": {"latitude": latitude + 0.008, "longitude": longitude - 0.002},
                    "is_closed": False
                },
                {
                    "id": "starbucks-mission-sf",
                    "name": "Starbucks",
                    "rating": 3.8,
                    "review_count": 432,
                    "price": "$",
                    "distance": 234.1,
                    "categories": ["Coffee & Tea"],
                    "address": ["2727 Mission St", "San Francisco, CA 94110"],
                    "phone": "+14156481420",
                    "coordinates": {"latitude": latitude + 0.002, "longitude": longitude + 0.001},
                    "is_closed": False
                }
            ],
            "restaurants": [
                {
                    "id": "tartine-bakery-sf",
                    "name": "Tartine Bakery & Cafe",
                    "rating": 4.4,
                    "review_count": 3421,
                    "price": "$$",
                    "distance": 645.2,
                    "categories": ["Bakeries", "Cafes"],
                    "address": ["600 Guerrero St", "San Francisco, CA 94110"],
                    "phone": "+14154872600",
                    "coordinates": {"latitude": latitude + 0.006, "longitude": longitude + 0.004},
                    "is_closed": False
                },
                {
                    "id": "la-taqueria-sf",
                    "name": "La Taqueria",
                    "rating": 4.6,
                    "review_count": 2156,
                    "price": "$",
                    "distance": 892.7,
                    "categories": ["Mexican"],
                    "address": ["2889 Mission St", "San Francisco, CA 94110"],
                    "phone": "+14152857117",
                    "coordinates": {"latitude": latitude + 0.009, "longitude": longitude - 0.003},
                    "is_closed": False
                }
            ],
            "thai": [
                {
                    "id": "lers-ros-thai-sf",
                    "name": "Lers Ros Thai",
                    "rating": 4.2,
                    "review_count": 1832,
                    "price": "$$",
                    "distance": 723.4,
                    "categories": ["Thai"],
                    "address": ["730 Larkin St", "San Francisco, CA 94109"],
                    "phone": "+14159316917",
                    "coordinates": {"latitude": latitude + 0.007, "longitude": longitude + 0.002},
                    "is_closed": False
                }
            ]
        }

        term_lower = term.lower()

        for key in mock_data:
            if key in term_lower:
                return mock_data[key]

        if "food" in term_lower or "eat" in term_lower or not term:
            return mock_data["restaurants"]

        return mock_data["coffee"]

    def _get_mock_business_details(self) -> Dict[str, Any]:
        """Return mock business details"""
        return {
            "id": "blue-bottle-coffee-sf",
            "name": "Blue Bottle Coffee",
            "rating": 4.5,
            "review_count": 1523,
            "price": "$$",
            "categories": [{"title": "Coffee & Tea"}],
            "location": {
                "address1": "300 Webster St",
                "city": "San Francisco",
                "state": "CA",
                "zip_code": "94117"
            },
            "coordinates": {"latitude": 37.7749, "longitude": -122.4194},
            "photos": ["https://example.com/photo1.jpg"],
            "hours": [
                {
                    "open": [
                        {"start": "0700", "end": "1900", "day": 0},
                        {"start": "0700", "end": "1900", "day": 1},
                        {"start": "0700", "end": "1900", "day": 2},
                        {"start": "0700", "end": "1900", "day": 3},
                        {"start": "0700", "end": "1900", "day": 4},
                        {"start": "0800", "end": "1800", "day": 5},
                        {"start": "0800", "end": "1800", "day": 6}
                    ]
                }
            ],
            "transactions": ["pickup", "delivery"],
            "is_closed": False
        }

    async def close(self):
        await self.client.aclose()