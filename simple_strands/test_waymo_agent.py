"""
Test Suite for Waymo Rider Experience Agent
Tests all components: Strands integration, Google Places API, and response formatting
"""

import unittest
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock
import math

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from waymo_rider_agent import (
    get_waymo_destination,
    search_places_near_destination,
    get_place_type,
    calculate_distance,
    format_distance,
    format_rider_response,
    WAYMO_DESTINATIONS
)

class TestWaymoRiderAgent(unittest.TestCase):
    """Test suite for Waymo Rider Experience Agent"""

    def test_get_waymo_destination(self):
        """Test that mock Waymo destinations are returned correctly"""
        destination = get_waymo_destination()

        # Check structure
        self.assertIn('lat', destination)
        self.assertIn('lng', destination)
        self.assertIn('name', destination)

        # Check it's from our mock destinations
        valid_names = [d['name'] for d in WAYMO_DESTINATIONS.values()]
        self.assertIn(destination['name'], valid_names)

        # Check coordinates are valid
        self.assertTrue(-90 <= destination['lat'] <= 90)
        self.assertTrue(-180 <= destination['lng'] <= 180)

    def test_get_place_type(self):
        """Test place type mapping"""
        # Test direct mappings
        self.assertEqual(get_place_type("coffee"), "coffee_shop")
        self.assertEqual(get_place_type("restaurant"), "restaurant")
        self.assertEqual(get_place_type("gas station"), "gas_station")
        self.assertEqual(get_place_type("hotel"), "lodging")

        # Test case insensitivity
        self.assertEqual(get_place_type("COFFEE"), "coffee_shop")
        self.assertEqual(get_place_type("Coffee Shop"), "coffee_shop")

        # Test phrases containing keywords
        self.assertEqual(get_place_type("best coffee nearby"), "coffee_shop")
        self.assertEqual(get_place_type("I need food"), "restaurant")

        # Test default fallback
        self.assertEqual(get_place_type("random query"), "restaurant")

    def test_calculate_distance(self):
        """Test distance calculation between coordinates"""
        # Same point should be 0
        distance = calculate_distance(37.7749, -122.4194, 37.7749, -122.4194)
        self.assertEqual(distance, 0)

        # Known distance test (approximately 1km)
        distance = calculate_distance(37.7749, -122.4194, 37.7840, -122.4194)
        self.assertTrue(900 < distance < 1100)  # Should be ~1km

        # Test symmetric property
        dist1 = calculate_distance(37.7749, -122.4194, 37.7840, -122.4090)
        dist2 = calculate_distance(37.7840, -122.4090, 37.7749, -122.4194)
        self.assertEqual(dist1, dist2)

    def test_format_distance(self):
        """Test distance formatting for display"""
        # Very close
        self.assertEqual(format_distance(50), "right at your destination")

        # Short walk (under 500m)
        self.assertEqual(format_distance(300), "300 meters away")

        # Medium walk (500-1000m, uses 60m per minute)
        self.assertEqual(format_distance(800), "800 meters (13 min walk)")

        # Longer distance (>1000m, uses 80m per minute)
        result = format_distance(1500)
        self.assertIn("1.5 km", result)
        self.assertIn("18 min walk", result)  # 1500/80 = 18.75 -> 18

    @patch('waymo_rider_agent.requests.post')
    def test_search_places_near_destination_success(self, mock_post):
        """Test successful Google Places API call"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'places': [
                {
                    'displayName': {'text': 'Test Coffee Shop'},
                    'formattedAddress': '123 Test St',
                    'rating': 4.5,
                    'userRatingCount': 100,
                    'location': {'latitude': 37.775, 'longitude': -122.418},
                    'currentOpeningHours': {'openNow': True},
                    'reviews': []
                }
            ]
        }
        mock_post.return_value = mock_response

        # Test search
        destination = {'lat': 37.7749, 'lng': -122.4194}
        places = search_places_near_destination('coffee', destination)

        # Verify results
        self.assertEqual(len(places), 1)
        self.assertEqual(places[0]['name'], 'Test Coffee Shop')
        self.assertEqual(places[0]['rating'], 4.5)
        self.assertEqual(places[0]['review_count'], 100)
        self.assertTrue(places[0]['open_now'])

        # Verify API was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn('places.googleapis.com', call_args[0][0])

    @patch('waymo_rider_agent.requests.post')
    def test_search_places_near_destination_failure(self, mock_post):
        """Test handling of API failures"""
        # Mock API error
        mock_response = Mock()
        mock_response.status_code = 403
        mock_post.return_value = mock_response

        # Test search
        destination = {'lat': 37.7749, 'lng': -122.4194}
        places = search_places_near_destination('coffee', destination)

        # Should return empty list, no mock data
        self.assertEqual(places, [])

    def test_format_rider_response_with_places(self):
        """Test formatting response with places found"""
        places = [
            {
                'name': 'Coffee Shop A',
                'distance_meters': 200,
                'distance_text': '200 meters (3 min walk)',
                'rating': 4.5,
                'review_count': 150,
                'open_now': True,
                'summary': 'Great coffee and pastries'
            },
            {
                'name': 'Coffee Shop B',
                'distance_meters': 500,
                'distance_text': '500 meters (6 min walk)',
                'rating': 4.0,
                'review_count': 80,
                'open_now': False,
                'summary': ''
            }
        ]

        response = format_rider_response('coffee', places, 'Downtown SF')

        # Check key elements are in response
        self.assertIn('Downtown SF', response)
        self.assertIn('Coffee Shop A', response)
        self.assertIn('4.5 stars', response)
        self.assertIn('150 reviews', response)
        self.assertIn('Open now', response)
        self.assertIn('200 meters', response)

    def test_format_rider_response_no_places(self):
        """Test formatting response when no places found"""
        response = format_rider_response('coffee', [], 'Downtown SF')

        self.assertIn("couldn't find", response.lower())
        self.assertIn('coffee', response)
        self.assertIn('Downtown SF', response)

    def test_integration_mock_destination_types(self):
        """Test that all mock destinations have required fields"""
        for key, dest in WAYMO_DESTINATIONS.items():
            self.assertIsInstance(dest['lat'], (int, float))
            self.assertIsInstance(dest['lng'], (int, float))
            self.assertIsInstance(dest['name'], str)
            self.assertTrue(-90 <= dest['lat'] <= 90)
            self.assertTrue(-180 <= dest['lng'] <= 180)

    @patch('waymo_rider_agent.requests.post')
    def test_real_api_integration(self, mock_post):
        """Test full integration with mocked API response"""
        # Mock API response with multiple places
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'places': [
                {
                    'displayName': {'text': 'Blue Bottle Coffee'},
                    'formattedAddress': '300 Webster St',
                    'rating': 4.5,
                    'userRatingCount': 523,
                    'location': {'latitude': 37.776, 'longitude': -122.419},
                    'currentOpeningHours': {'openNow': True},
                    'editorialSummary': {'text': 'Popular third-wave coffee shop'},
                    'reviews': [
                        {'text': {'text': 'Great coffee!'}},
                        {'text': {'text': 'Love the atmosphere'}}
                    ]
                },
                {
                    'displayName': {'text': 'Starbucks'},
                    'formattedAddress': '100 Market St',
                    'rating': 3.8,
                    'userRatingCount': 200,
                    'location': {'latitude': 37.774, 'longitude': -122.420},
                    'currentOpeningHours': {'openNow': True},
                    'reviews': []
                }
            ]
        }
        mock_post.return_value = mock_response

        # Get destination and search
        destination = {'lat': 37.7749, 'lng': -122.4194, 'name': 'Downtown SF'}
        places = search_places_near_destination('coffee', destination, 2000)

        # Verify we got both places
        self.assertEqual(len(places), 2)

        # Verify sorting by distance (Starbucks should be closer)
        self.assertTrue(places[0]['distance_meters'] < places[1]['distance_meters'])

        # Format response
        response = format_rider_response('coffee', places, destination['name'])

        # Verify formatted response includes both
        self.assertIn('Blue Bottle Coffee', response)
        self.assertIn('Starbucks', response)
        self.assertIn('Downtown SF', response)

def run_tests():
    """Run all tests and return success status"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestWaymoRiderAgent)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return True if all tests passed
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)