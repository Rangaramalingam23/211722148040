from flask import Flask, jsonify
import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

AUTH_URL = os.getenv("AUTH_URL")
NUMBER_TYPE_URLS = {
    "p": os.getenv("PRIME_URL"),
    "f": os.getenv("FIBO_URL"),
    "e": os.getenv("EVEN_URL"),
    "r": os.getenv("RAND_URL")
}
AUTH_PAYLOAD = {
    "email": os.getenv("EMAIL"),
    "name": os.getenv("NAME"),
    "rollNo": os.getenv("ROLL_NO"),
    "accessCode": os.getenv("ACCESS_CODE"),
    "clientID": os.getenv("CLIENT_ID"),
    "clientSecret": os.getenv("CLIENT_SECRET")
}

access_token = None
token_expiry = 0
number_window = []
window_size = 10

def refresh_token():
    global access_token
    global token_expiry

    try:
        response = requests.post(AUTH_URL, json=AUTH_PAYLOAD, timeout=5)
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            access_token = data.get("access_token")
            expires_in = data.get("expires_in", 300)
            if expires_in > 3600:
                expires_in = 300
            token_expiry = time.time() + expires_in
            print("Token refreshed")
        else:
            print("Token refresh failed:", response.text)
            access_token = None
    except Exception as err:
        print("Error during token refresh:", str(err))
        access_token = None

def get_numbers_from_server(number_type):
    if number_type not in NUMBER_TYPE_URLS:
        print("Invalid type:", number_type)
        return []

    global access_token, token_expiry

    if access_token is None or time.time() > token_expiry:
        refresh_token()

    if access_token is None:
        print("Access token not available.")
        return []

    headers = {
        "Authorization": "Bearer " + access_token
    }

    try:
        url = NUMBER_TYPE_URLS[number_type]
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            data = res.json()
            print("Numbers fetched:", data.get("numbers", []))
            return data.get("numbers", [])
        else:
            print("Fetch failed:", res.text)
            return []
    except Exception as ex:
        print("Exception in fetching:", str(ex))
        return []

@app.route("/numbers/<number_type>", methods=["GET"])
def calculate_average(number_type):
    global number_window

    prev_state = number_window.copy()
    new_numbers = get_numbers_from_server(number_type)

    if not new_numbers and access_token is None:
        return jsonify({"error": "Failed to authenticate with the server"}), 500

    for number in new_numbers:
        if number not in number_window:
            number_window.append(number)
            if len(number_window) > window_size:
                number_window.pop(0)

    avg = 0.0
    if len(number_window) > 0:
        avg = round(sum(number_window) / len(number_window), 2)

    return jsonify({
        "windowPrevState": prev_state,
        "windowCurrState": number_window,
        "numbers": new_numbers,
        "avg": avg
    })

if __name__ == "__main__":
    app.run(port=9876)
