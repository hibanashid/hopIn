# Copy the content from @copy_of_untitled6.py here
# Make sure to adapt the function to return a list of dictionaries
# where each dictionary represents a day with activities

import googlemaps
import google.generativeai as genai
from datetime import datetime, timedelta
from geopy.distance import geodesic
from geopy.distance import great_circle
import json
import os
import requests
from geopy.geocoders import Nominatim
from requests.exceptions import ReadTimeout, ConnectionError
from google.generativeai import GenerativeModel
from itertools import combinations
import re
import os
from dotenv import load_dotenv
import logging
from tenacity import retry, stop_after_attempt, wait_fixed

load_dotenv()
print("GOOGLE_MAPS_API_KEY:", os.getenv('GOOGLE_MAPS_API_KEY'))

# Load environment variables
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not GOOGLE_MAPS_API_KEY:
    raise ValueError("GOOGLE_MAPS_API_KEY is not set in the environment variables")
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
ORS_API_KEY = os.getenv("ORS_API_KEY")

# Initialize clients and services
geolocator = Nominatim(user_agent="itinerary_generator")
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
genai.configure(api_key=GOOGLE_AI_API_KEY)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_places(destination, place_type, food_preference=None):
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    
    if place_type == "restaurant" and food_preference:
        query = f"{food_preference} restaurant in {destination}"
    else:
        query = f"{place_type} in {destination}"
    
    params = {
        'query': query,
        'key': GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] != 'OK':
            logger.error(f"Error in Google Places API: {data['status']}")
            return []
        
        places = []
        for result in data['results'][:5]:  # Limit to top 5 results
            place = {
                'name': result['name'],
                'rating': result.get('rating'),
                'address': result.get('formatted_address'),
                'place_id': result['place_id'],
                'location': result['geometry']['location']
            }
            places.append(place)
        
        return places
    
    except requests.RequestException as e:
        logger.error(f"Error fetching places from Google Maps API: {str(e)}")
        return []

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def calculate_distance(origin, destination):
    base_url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': ORS_API_KEY,
        'Content-Type': 'application/json; charset=utf-8'
    }
    body = {
        "coordinates": [[origin['lng'], origin['lat']], [destination['lng'], destination['lat']]]
    }
    
    try:
        response = requests.post(base_url, json=body, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Log the entire response for debugging
        logger.debug(f"ORS API Response: {data}")
        
        # Check if the expected keys exist
        if 'routes' in data and data['routes'] and 'summary' in data['routes'][0]:
            summary = data['routes'][0]['summary']
            if 'distance' in summary:
                distance_km = summary['distance'] / 1000
                return f"{distance_km:.2f} km"
            else:
                logger.error("Distance key not found in the response summary")
                return "Distance calculation failed"
        else:
            logger.error("Unexpected response structure from ORS API")
            return "Distance calculation failed"
    
    except requests.RequestException as e:
        logger.error(f"Error calculating distance using ORS API: {str(e)}")
        return "Distance calculation failed"
    except KeyError as e:
        logger.error(f"KeyError in calculate_distance: {str(e)}")
        return "Distance calculation failed"
    except Exception as e:
        logger.error(f"Unexpected error in calculate_distance: {str(e)}")
        return "Distance calculation failed"

# Add this function to get more details about a place
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_place_details(place_id):
    base_url = "https://maps.googleapis.com/maps/api/place/details/json"
    
    params = {
        'place_id': place_id,
        'fields': 'name,rating,formatted_phone_number,website,review,url',
        'key': GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] != 'OK':
            logger.error(f"Error in Google Place Details API: {data['status']}")
            return None
        
        result = data['result']
        details = {
            'name': result.get('name'),
            'rating': result.get('rating'),
            'phone': result.get('formatted_phone_number'),
            'website': result.get('website'),
            'google_maps_url': result.get('url'),
            'review': result.get('reviews', [{}])[0].get('text', 'No review available')
        }
        
        return details
    
    except requests.RequestException as e:
        logger.error(f"Error fetching place details from Google Maps API: {str(e)}")
        return None

def generate_itinerary(destination: str, no_of_days: int, food_preference: str):
    try:
        logger.info(f"Starting itinerary generation for {destination}, {no_of_days} days, {food_preference}")
        
        attractions = get_places(destination, "tourist attraction")
        logger.debug(f"Attractions: {attractions}")

        restaurants = get_places(destination, "restaurant", food_preference)
        logger.debug(f"Restaurants: {restaurants}")

        accommodations = get_places(destination, "hotel")
        logger.debug(f"Accommodations: {accommodations}")

        # Get more details for each place
        all_places = attractions + restaurants + accommodations
        for place in all_places:
            details = get_place_details(place['place_id'])
            if details:
                place.update(details)

        attractions_data = json.dumps(attractions)
        restaurants_data = json.dumps(restaurants)
        accommodations_data = json.dumps(accommodations)

        prompt = f"""
        Generate a detailed, day-by-day itinerary for a trip to {destination} for {no_of_days} days.
        The traveler prefers {food_preference} food.

        Use the following data to create the itinerary:
        Tourist Attractions: {attractions_data}
        Restaurants: {restaurants_data}
        Accommodations: {accommodations_data}

        Instructions:
        - Organize the itinerary based on the user's specified number of days.
        - For each day, include breakfast, 2-3 tourist attractions, lunch, dinner, and accommodation.
        - Consider proximity of locations and food preferences.
        - Include timings, Google Maps URLs, website links, ratings, and brief descriptions.

        Output Format:
        Format the itinerary as a valid JSON object with a key for each day of the trip.
        Each day should contain a list of activities structured as follows:
        {{
          "Day 1": [
            {{
              "time": "8:00 AM",
              "activity": "Breakfast",
              "place_name": "Restaurant Name",
              "description": "Brief description",
              "rating": 4.5,
              "review": "Short review",
              "google_maps_url": "https://maps.google.com/...",
              "website_url": "https://example.com",
              "estimated_travel_time": "N/A",
              "location": {{"lat": 12.3456, "lng": 78.9012}}
            }},
            // ... more activities for Day 1
          ],
          // ... more days
        }}
        """

        logger.debug("Sending prompt to Gemini model")
        model = GenerativeModel('gemini-1.5-pro-002')
        response = model.generate_content(prompt)
        logger.debug(f"Received response from Gemini model: {response}")

        content_text = response.text
        logger.debug(f"Extracted content text: {content_text}")

        json_text_match = re.search(r"{.*}", content_text, re.DOTALL)

        if json_text_match:
            json_text = json_text_match.group(0).strip()
            logger.debug(f"Extracted JSON text: {json_text}")

            try:
                itinerary_data = json.loads(json_text)
                logger.debug(f"Parsed itinerary data: {itinerary_data}")

                for day, activities in itinerary_data.items():
                    for i in range(len(activities) - 1):
                        origin = activities[i].get('location', {})
                        destination = activities[i+1].get('location', {})
                        if origin and destination:
                            distance = calculate_distance(origin, destination)
                            activities[i]['distance_to_next'] = distance
                        else:
                            activities[i]['distance_to_next'] = "Location data unavailable"

                    if activities:
                        activities[-1]['distance_to_next'] = "N/A"

                logger.info("Itinerary generation completed successfully")
                return itinerary_data
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON: {e}")
                logger.error(f"Problematic JSON: {json_text}")
                return None
        else:
            logger.error("No JSON content found in response.")
            return None
    except Exception as e:
        logger.exception(f"Error in generate_itinerary: {str(e)}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def call_external_api():
    # Your API call here
    pass


