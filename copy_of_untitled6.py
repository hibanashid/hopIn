

import streamlit as st
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

GOOGLE_MAPS_API_KEY = ""
GOOGLE_AI_API_KEY = ""

ORS_API_KEY = ""

# Initialize Nominatim geocoder
geolocator = Nominatim(user_agent="itinerary_generator")

# anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

genai.configure(api_key=GOOGLE_AI_API_KEY)

def calculate_distance(origin, destination):
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': ORS_API_KEY,
        'Content-Type': 'application/json; charset=utf-8'
    }
    data = {
        "coordinates": [
            [origin['lng'], origin['lat']],
            [destination['lng'], destination['lat']]
        ]
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        routes = response.json()['routes']
        if routes:
            return round(routes[0]['summary']['distance'] / 1000, 1)  # Convert to km and round to 1 decimal
        else:
            print(f"No route found between {origin} and {destination}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error calculating distance: {e}")
        return None

def get_places(location, place_type, food_type=None):
    query = f"{place_type} in {location}"
    if food_type:
        query = f"{food_type} {query}"

    places_result = gmaps.places(query=query)
    detailed_places = []

    for place in places_result.get('results', [])[:10]:  # Limit to top 5 results
        place_id = place['place_id']
        details = gmaps.place(place_id=place_id, fields=['name', 'formatted_address', 'rating', 'url', 'website', 'opening_hours', 'price_level', 'reviews','geometry'])

        detailed_place = {
            "name": details['result'].get('name'),

            "rating": details['result'].get('rating'),
            "google_maps_url": details['result'].get('url'),
            "website": details['result'].get('website'),

            # "opening_hours": details['result'].get('opening_hours', {}).get('weekday_text', []),
            "location": details['result']['geometry']['location']}

        detailed_places.append(detailed_place)

    return detailed_places



import re

def generate_itinerary(destination, no_of_days, food_preference):
    # Get tourist attractions
    attractions = get_places(destination, "tourist attraction")

    # Get restaurants based on food preference
    restaurants = get_places(destination, "restaurant", food_preference)

    # Get accommodations
    accommodations = get_places(destination, "hotel")

    # Prepare data for Gemini
    attractions_data = json.dumps(attractions)
    restaurants_data = json.dumps(restaurants)
    accommodations_data = json.dumps(accommodations)

    # Prepare the prompt for Gemini
    prompt = f"""
    You are an intelligent AI assiatant.Generate a detailed, day-by-day itinerary for a trip to {destination} for {no_of_days} number of days. Ensure that the number of days is considered when creating the response.
please create itinerary for each day considering {no_of_days}.please dont give itinerary for few days.
The traveler prefers {food_preference} food.

Use the following data to create the itinerary:
Tourist Attractions: {attractions_data}
Restaurants: {restaurants_data}
Accommodations: {accommodations_data}
Instructions:
Organize the itinerary based on the user's specified start and end dates.
For each day, begin with breakfast, followed by 2-3 tourist attractions, and schedule lunch and dinner at appropriate times.
End each day with a suggested accommodation for overnight stays.
Consider the proximity of locations, activity duration, and food preferences.
Include approximate timings for each activity throughout the day.
Provide Google Maps URL and website links (if available) for each place, along with a brief description including opening hours, ratings, and a short review.
Calculate the estimated travel time between locations to ensure a logical flow of activities.
Output Format:
Format the itinerary as a valid JSON object.
The output should have a key for each day of the trip.
Each day should contain a list of activities structured as follows.give a itinerary in json format for each day separately.
please create itinerary for each day considering {no_of_days}.you can repeat restaurants if needed, but dont repeat tourist spot.please dont give itinerary for few days.give itinerary for each day
(please dont give comments like  // ... (Day 2, Day 3, and Day 4 will follow a similar structure or  // ... (Day 3 and Day 4 will be here) instead of itinerary)):
{{
  "Day 1": [
    {{
      "time": "8:00 AM",
      "activity": "Breakfast",
      "place_name": "Restaurant 1",
      "description": "A cozy cafe offering a great breakfast menu...",
      "rating": 4.5,
      "review": "Great atmosphere and excellent breakfast options!",
      "google_maps_url": "https://maps.google.com/...",
      "website_url": "https://restaurant1.com",


      "estimated_travel_time": "N/A",
      "location": {{"lat": 12.3456, "lng": 78.9012}}
    }},
    {{
      "time": "9:30 AM",
      "activity": "Visit Attraction 1",
      "place_name": "Museum of Natural History",
      "description": "A renowned museum featuring exhibits on natural history...",
      "rating": 4.7,
      "review": "A must-see for history enthusiasts...",
      "google_maps_url": "https://maps.google.com/...",
      "website_url": "https://museum.com",

      "estimated_travel_time": "15 min",
      "location": {{"lat": 12.3456, "lng": 78.9012}}

    }},
    {{
      "time": "12:30 PM",
      "activity": "Lunch",
      "place_name": "Restaurant 2",
      "description": "Famous for its vegetarian options...",
      "rating": 4.6,
      "review": "Delicious vegetarian meals with quick service.",
      "google_maps_url": "https://maps.google.com/...",
      "website_url": "https://restaurant2.com",
      "estimated_travel_time": "10 min",
      "location": {{"lat": 12.3456, "lng": 78.9012}}
    }},
    {{
      "time": "6:00 PM",
      "activity": "Check-in at Accommodation",
      "place_name": "Hotel Sunshine",
      "description": "A 4-star hotel with excellent amenities...",
      "rating": 4.8,
      "review": "Comfortable rooms and great service.",
      "google_maps_url": "https://maps.google.com/...",
      "website_url": "https://hotel-sunshine.com",
      "estimated_travel_time": "N/A",
      "location": {{"lat": 12.3456, "lng": 78.9012}}
    }}
  ],
  "Day 2": [
    {{
      "time": "8:00 AM",
      "activity": "Breakfast",
      "place_name": "Restaurant 3",
      "description": "Modern cafe offering continental breakfast...",
      "rating": 4.3,
      "review": "Good food, quick service!",
      "google_maps_url": "https://maps.google.com/...",
      "website_url": "https://restaurant3.com",
      "estimated_travel_time": "N/A",
      "location": {{"lat": 12.3456, "lng": 78.9012}}
    }},
    {{
      "time": "10:00 AM",
      "activity": "Visit Attraction 2",
      "place_name": "Central Park",
      "description": "A large urban park with beautiful walking trails...",
      "rating": 4.9,
      "review": "Beautiful scenery and relaxing atmosphere.",
      "google_maps_url": "https://maps.google.com/...",
      "website_url": "https://centralpark.com",
      "estimated_travel_time": "20 min",
      "location": {{"lat": 12.3456, "lng": 78.9012}}
    }}

  ]
}}


    """

    # Set up Gemini model
    model = GenerativeModel('gemini-1.5-pro-002')

    # Generate content
    response = model.generate_content(prompt)

    try:
        # Access the JSON content within the response object
        content_text = response.candidates[0].content.parts[0].text
    except (KeyError, TypeError, AttributeError) as e:
        print("Error accessing the response structure:", e)
        return None

    json_text_match = re.search(r"{.*}", content_text, re.DOTALL)

    if json_text_match:
        json_text = json_text_match.group(0).strip()  # Extract matched JSON text
        # print("Extracted JSON text:\n", json_text)  # Debugging output

        # Parse the JSON content
        try:
            itinerary_data = json.loads(json_text)

            for day, activities in itinerary_data.items():

              for i in range(len(activities) - 1):
                origin = activities[i].get('location', {})
                # return origin
                destination = activities[i+1].get('location', {})
                # return destination
                if origin and destination:
                    distance = calculate_distance(origin, destination)

                    activities[i]['distance_to_next'] = distance if distance is not None else "Unable to calculate"

                else:
                    activities[i]['distance_to_next'] = "Location data unavailable"

            # Set the distance_to_next for the last activity of the day to "N/A"
                if activities:
                    activities[-1]['distance_to_next'] = "N/A"

            return itinerary_data
        except json.JSONDecodeError as e:
            print("Error parsing JSON:", e)
            print("Problematic JSON:", json_text)
            return None
    else:
        print("No JSON content found in response.")
        return None



   

