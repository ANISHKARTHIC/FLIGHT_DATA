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
                # Use the airline name from the 'carrierCode' field (not 'validatingAirlineCodes')
                flight_name = flight["validatingAirlineCodes"][0] if "validatingAirlineCodes" in flight else "Unknown Airline"
                matching_flights.append({
                    "from": segment["departure"]["iataCode"],
                    "to": segment["arrival"]["iataCode"],
                    "price": flight["price"]["total"],
                    "time": flight_time_str,
                    "flight_name": flight_name,  # Flight name
                })
    return matching_flights

# Step 5: Convert price from USD to INR
def convert_price_to_inr(usd_price):
    return round(float(usd_price) * USD_TO_INR, 2)

# Step 6: Streamlit UI

# Set Streamlit page config (to include dark mode toggle and overall style)
st.set_page_config(page_title="Flight Search Tool", page_icon="✈️", layout="centered")

# Custom CSS Styling for Dark and Light Mode
st.markdown("""
    <style>
        .title {
            text-align: center;
            color: #ff6347; /* Tomato color for an attractive title */
            font-size: 50px;
            font-family: 'Verdana', sans-serif;
            font-weight: bold;
        }
        .header {
            text-align: center;
            font-size: 24px;
            color: #007BFF;
        }
        .widget {
            margin: 20px;
        }
        .result {
            background-color: #f2f2f2;
            padding: 10px;  /* Reduced padding to avoid large empty space */
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            margin-bottom: 10px;  /* Reduced margin */
            transition: all 0.3s ease;
        }
        .result:hover {
            transform: scale(1.05);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
        }
        .result-dark {
            background-color: #333333;
            color: white;
            padding: 10px;  /* Reduced padding */
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5);
            margin-bottom: 10px;  /* Reduced margin */
            transition: all 0.3s ease;
        }
        .result-dark:hover {
            transform: scale(1.05);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.7);
        }
        .airport-list {
            text-align: center;
            font-size: 18px;
            color: #4CAF50;
            font-weight: bold;
        }
        .button {
            background-color: #007BFF;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            border: none;
            cursor: pointer;
            font-size: 16px;
        }
        .button:hover {
            background-color: #0056b3;
        }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="title">Flight Search Tool</div>', unsafe_allow_html=True)

# Available airport codes for selection (with airport names)
airport_codes = {
    'JFK': 'New York (JFK)', 'LAX': 'Los Angeles (LAX)', 'ORD': 'Chicago (ORD)',
    'BOM': 'Mumbai (BOM)', 'DEL': 'Delhi (DEL)', 'BLR': 'Bangalore (BLR)',
    'MAA': 'Chennai (MAA)', 'CJB': 'Coimbatore (CJB)'
}

# Display airport codes and names
st.markdown('<div class="airport-list">Available Airport Codes:</div>', unsafe_allow_html=True)
for code, name in airport_codes.items():
    st.markdown(f"- **{code}: {name}**")

# User input
col1, col2 = st.columns(2)

with col1:
    origin = st.selectbox("Select the origin airport code:", list(airport_codes.keys()), key="origin", label_visibility="collapsed")
with col2:
    destination = st.selectbox("Select the destination airport code:", list(airport_codes.keys()), key="destination", label_visibility="collapsed")

# Departure Date and Time Inputs
departure_date = st.date_input("Select the departure date:", key="departure_date", label_visibility="collapsed")
query_time = st.time_input("Select the time for search:", key="query_time", label_visibility="collapsed")

# Search Button
if st.button("Search Flights", key="search_button", use_container_width=True):
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
                    st.subheader("Flights within 1-hour range:", anchor="flights", help="Results for flights within 1 hour of your selected time")
                    for flight in results:
                        # Use dark mode style when it's activated
                        result_class = "result-dark" if st.session_state.get('dark_mode', False) else "result"
                        st.markdown(f"""
                            <div class="{result_class}">
                                <strong>Flight Name:</strong> {flight['flight_name']}<br>
                                <strong>From:</strong> {flight['from']}<br>
                                <strong>To:</strong> {flight['to']}<br>
                                <strong>Price:</strong> ₹{flight['price_inr']}<br>
                                <strong>Time:</strong> {flight['time']}
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.write("No flights found within the 1-hour range.")
            else:
                st.write("No flight offers available.")
    else:
        st.error("Please fill in all the fields.")
