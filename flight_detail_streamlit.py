import streamlit as st
import requests
import datetime
import json

# Step 1: Define API credentials and endpoints
API_KEY = "9FqzYSKweLsFi48ORHpNwyPYJ4OdyC8N"
API_SECRET = "r3YlrQRPj8rAKrWB"
AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
FLIGHT_OFFERS_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

# Hardcoded USD to INR conversion rate (you can replace this with an API for live conversion)
USD_TO_INR = 83.0

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
        st.error("Authentication Error: " + str(response.status_code))
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
        st.error("Error fetching flight offers: " + str(response.status_code))
        return []

# Step 4: Function to find flights within a 1-hour range
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

# Step 5: Convert price from USD to INR
def convert_price_to_inr(usd_price):
    return round(float(usd_price) * USD_TO_INR, 2)

# Step 6: Streamlit UI
st.title("Flight Search Tool")

# Available airport codes for selection (you can replace this list with real data)
airport_codes = ['JFK(New York)', 'LAX(Los Angeles)', 'ORD(Chicago)', 'BOM(BOMBAY)', 'DEL(DELHI)', 'BLR(Bangalore)', 'MAA (CHENNAI )','CJB (COIMBATORE)']

# User input
origin = st.selectbox("Select the origin airport code:", airport_codes)
destination = st.selectbox("Select the destination airport code:", airport_codes)
departure_date = st.date_input("Enter the departure date (YYYY-MM-DD):")
query_time = st.time_input("Enter the time to search for flights (HH:MM):")

if st.button("Search Flights"):
    if origin and destination and departure_date and query_time:
        # Authenticate and get the access token
        token = get_access_token()
        if token:
            # Fetch flight offers
            flight_offers = fetch_flight_offers(token, origin.upper(), destination.upper(), departure_date)
            
            if flight_offers:
                # Find flights within the 1-hour time range
                results = find_flights_within_time_range(flight_offers, query_time.strftime("%H:%M"))
                
                # Convert prices to INR
                for flight in results:
                    flight["price_inr"] = convert_price_to_inr(flight["price"])
                
                # Display results
                if results:
                    st.subheader("Flights within 1-hour range:")
                    for flight in results:
                        st.write(f"From: {flight['from']}, To: {flight['to']}, Price: ₹{flight['price_inr']}, Time: {flight['time']}")
                else:
                    st.write("No flights found within the 1-hour range.")
            else:
                st.write("No flight offers available.")
    else:
        st.error("Please fill in all the fields.")
