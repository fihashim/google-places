# This is a jupyter notebook which extracts 400 restaurants in Berlin and filters out hotels or lodgings in batches of 20. 
# The data is then stored in a pandas dataframe and visualized on a map using folium.
import requests
import pandas as pd
import random
import folium
import math
import requests

API_KEY = "YOUR_API_KEY"
lat_center = 52.5200  # Latitude of Berlin
lon_center = 13.4050  # Longitude of Berlin

# Function to generate random coordinates within a given radius from a center point
def generate_random_coordinates(lat_center, lon_center, radius_km):
    # Convert radius from kilometers to degrees (approximately)
    radius_deg = radius_km / 110.574  # Approx conversion factor for latitude/longitude
    random_lat = lat_center + random.uniform(-radius_deg, radius_deg)
    random_lon = lon_center + random.uniform(-radius_deg, radius_deg)
    return random_lat, random_lon

# Function to fetch restaurants near a location
def get_restaurants_near_location(lat_center, lon_center, api_key, radius=500, num_results=20):
    """Fetch restaurant place IDs near a given location using the Google Places API."""
    endpoint_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        'location': f'{lat_center},{lon_center}',
        'radius': radius,
        'type': ['restaurant', 'cafe', 'bar'],
        'key': api_key
    }
    
    response = requests.get(endpoint_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        return results[:num_results]  # Limit to the number of results (20)
    else:
        print(f"Error fetching data: {response.status_code}")
        return []

# Function to fetch place details and filter out hotels or lodgings
def get_place_details(place_id, api_key):
    """Fetch detailed place information for a specific place ID using the Place Details API."""
    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        'place_id': place_id,
        'fields': 'name,editorial_summary,vicinity,opening_hours,rating,reviews,types,price_level,user_ratings_total,geometry',  # Add 'types' to filter places
        'key': api_key
    }
    
    response = requests.get(details_url, params=params)
    
    if response.status_code == 200:
        place_details = response.json().get('result', {})
        return place_details
    else:
        print(f"Error fetching place details: {response.status_code}")
        return {}

if __name__ == '__main__':
        # Initialize list to hold restaurant data for batching
    batch_restaurant_data = []
    batch_size = 20  # Number of rows per batch
    saved_rows = 0  # Track the total number of saved rows
    total_required = 400  # Total number of unique rows to be saved

    # Keep track of the number of unique rows
    unique_rows = set()

    # Continue fetching data until we have 1000 unique rows
    while saved_rows < total_required:
        # Generate a random coordinate within a 6km radius of the center
        random_lat, random_lon = generate_random_coordinates(lat_center, lon_center, radius_km=6)

        # Step 1: Fetch restaurants near the location
        restaurants = get_restaurants_near_location(random_lat, random_lon, API_KEY, radius=500, num_results=20)

        # Step 2: For each restaurant, fetch detailed information and store it in a list
        for restaurant in restaurants:
            place_id = restaurant.get('place_id')

            # Skip if we've already processed this place ID
            if place_id in unique_rows:
                continue

            place_details = get_place_details(place_id, API_KEY)

            # Check if the place is categorized as a hotel or lodging and skip if so
            place_types = place_details.get('types', [])
            if 'lodging' in place_types or 'hotel' in place_types:
                continue  # Skip if the place is a hotel or lodging

            # Check if the place has an editorial summary
            editorial_summary = place_details.get('editorial_summary', {}).get('overview')

            if editorial_summary:
                # Fetch the restaurant details
                name = place_details.get('name', 'None')
                address = place_details.get('vicinity', 'None')
                latitude = place_details.get('geometry', {}).get('location', {}).get('lat', 'None')
                longitude = place_details.get('geometry', {}).get('location', {}).get('lng', 'None')
                opening_hours = place_details.get('opening_hours', {}).get('weekday_text', 'None')
                price_level = place_details.get('price_level', 'None')
                rating = place_details.get('rating', 'None')
                reviews = place_details.get('reviews', [])
                total_reviews = place_details.get('user_ratings_total', 'None')
                # Collect review text (up to 3 reviews)
                review_texts = [review.get('text', 'No review text') for review in reviews[:3]] if reviews else ['None']
                review_ratings = [review.get('rating', 'No rating') for review in reviews[:3]] if reviews else ['None']

                # Append the data to the batch list
                batch_restaurant_data.append({
                    'Place ID': place_id,
                    'Name': name,
                    'Summary': editorial_summary,
                    'Price Level': price_level,
                    'Address': address,
                    'Latitude': latitude,
                    'Longitude': longitude,
                    'Overall Rating': rating,
                    'Opening Hours': ', '.join(opening_hours) if isinstance(opening_hours, list) else opening_hours,
                    'Total Reviews': total_reviews,
                    'Reviews': review_texts,
                    'Review Ratings': review_ratings
                })

                # Add this place ID to the set of processed IDs to ensure uniqueness
                unique_rows.add(place_id)

                # Check if we reached the batch size limit
                if len(batch_restaurant_data) == batch_size:
                    # Convert batch to DataFrame and append it to CSV
                    df_batch = pd.DataFrame(batch_restaurant_data)
                    
                    # Save the batch to a CSV file
                    df_batch.to_csv('restaurants_data.csv', mode='a', header=(saved_rows == 0), index=False)
                    
                    # Reset batch data after saving
                    batch_restaurant_data = []
                    
                    # Increment saved rows count
                    saved_rows += batch_size
                    
                    # Print progress
                    print(f"Saved {saved_rows} rows so far.")

    # In case there are any remaining rows that didn't complete a batch of 50
    if batch_restaurant_data:
        df_batch = pd.DataFrame(batch_restaurant_data)
        df_batch.to_csv('restaurants_data.csv', mode='a', header=(saved_rows == 0), index=False)
        saved_rows += len(batch_restaurant_data)
        print(f"Final batch saved. Total rows saved: {saved_rows}")
