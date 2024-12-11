import requests
import datetime
import json

# Step 1: Define API credentials and endpoints
API_KEY = "9FqzYSKweLsFi48ORHpNwyPYJ4OdyC8N"
API_SECRET = "r3YlrQRPj8rAKrWB"
AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
FLIGHT_OFFERS_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

# Step 2: Function to authenticate and get the access token
def get_access_token():
    response = requests.post(
        AUTH_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": API_KEY,
            "client_secret": API_SECRET,
        }
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print("Authentication Error:", response.status_code, response.json())
        return None

# Step 3: Function to fetch flight offers based on user inputs
def fetch_flight_offers(access_token, origin, destination, departure_date):
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date,
        "adults": 1,
        "currencyCode": "USD",
    }
    response = requests.get(FLIGHT_OFFERS_URL, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print("Error fetching flight offers:", response.status_code, response.json())
        return []


# Step 4: Function to save API response to JSON
def save_to_json(data, file_name):
    try:
        with open(file_name, "w") as json_file:
            json.dump(data, json_file, indent=4)  # Save with pretty-print formatting
        print(f"Flight data saved to {file_name}")
    except Exception as e:
        print(f"Error saving to JSON: {e}")

# Step 5: Main program logic
if __name__ == "__main__":
    print("Welcome to the Flight Search Tool!")

    # User inputs
    origin = input("Enter the origin airport code (e.g., JFK): ").strip().upper()
    destination = input("Enter the destination airport code (e.g., LAX): ").strip().upper()
    departure_date = input("Enter the departure date (YYYY-MM-DD): ").strip()
    query_time = input("Enter the time to search for flights (HH:MM): ").strip()

    # Authenticate and get the access token
    token = get_access_token()
    if token:
        # Fetch flight offers
        flight_offers = fetch_flight_offers(token, origin, destination, departure_date)
        
        # Save raw flight offers to JSON
        save_to_json(flight_offers, "flight_details.json")

        # Find flights within the 1-hour time range
        def find_flights_within_time_range(flights, query_time):
            query_time = datetime.datetime.strptime(query_time, "%H:%M")  # Parse user input time
            matching_flights = []
            for flight in flights:
                for segment in flight["itineraries"][0]["segments"]:
                    flight_time_str = segment["departure"]["at"].split("T")[1][:5]
                    flight_time = datetime.datetime.strptime(flight_time_str, "%H:%M")
                    time_difference = abs((flight_time - query_time).total_seconds()) / 3600
                    if time_difference <= 1:  # Check if the time is within 1 hour
                        matching_flights.append({
                            "from": segment["departure"]["iataCode"],
                            "to": segment["arrival"]["iataCode"],
                            "price": flight["price"]["total"],
                            "time": flight_time_str,
                        })
            return matching_flights
        
        results = find_flights_within_time_range(flight_offers, query_time)
        
        # Save filtered results to JSON
        save_to_json(results, "filtered_flights.json")

        # Display results
        if results:
            print("\nFlights within 1-hour range:")
            for flight in results:
                print(f"From: {flight['from']}, To: {flight['to']}, Price: ${flight['price']}, Time: {flight['time']}")
        else:
            print("No flights found within the 1-hour range.")
    else:
        print("Unable to fetch flights. Please check your API credentials or connection.")
