# ===============================================
# --- IMPORTS & INITIALIZATION ---
# ===============================================
import os
import random
import requests
from flask import Flask, render_template, jsonify, request

# Initialize the Flask Application
app = Flask(__name__)

# ===============================================
# --- GROQ CONFIG (Non-intrusive addition) ---
# ===============================================
# Reads GROQ_API_KEY and optional GROQ_MODEL from the environment.
# If GROQ_API_KEY is not set, the app will continue to work exactly as before.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")
GROQ_BASE = "https://api.groq.com/openai/v1/chat/completions"

def call_groq_chat(user_prompt, system_prompt=None, max_tokens=512, temperature=0.2):
    """
    Correct Groq Chat Completion call.
    Uses:
        - messages[]
        - model
        - max_completion_tokens
    """
    if not GROQ_API_KEY:
        print("[Groq] API key not configured. Skipping.")
        return None

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_completion_tokens": max_tokens   # <--- THIS IS THE ONLY VALID ONE
    }

    try:
        print("[Groq] Sending request...")
        resp = requests.post(GROQ_BASE, headers=headers, json=payload, timeout=20)

        print("[Groq] Status:", resp.status_code)
        print("[Groq] Body:", resp.text)

        if resp.status_code != 200:
            return None

        data = resp.json()
        choice = data["choices"][0]

        # Try extracting message content
        msg = choice.get("message", {})
        content = msg.get("content")

        if not content:
            content = choice.get("text")

        return content.strip() if content else None

    except Exception as e:
        print("[Groq] Error:", e)
        return None

@app.route('/_debug_routes', methods=['GET'])
def debug_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(f"{rule.rule}  ->  {','.join(sorted(rule.methods))}")
    return "<pre>" + "\n".join(routes) + "</pre>"


# ===============================================
# --- GLOBAL STATE SIMULATION ---
# ===============================================
# This dictionary acts as a mini-database for smart home device states.
smart_home_devices = {
    "Living Room Lamp": "Off",
    "Bedroom Fan": "Off",
    "Kitchen Outlet": "On"
}

# ===============================================
# --- AI AGENT TOOL SIMULATION ---
# These functions simulate the "tools" our AI Agent can use.
# In a real system, these would trigger n8n workflows or AutoGen agents.
# ===============================================

def tool_book_ride(destination="an unknown location"):
    print(f"[Agent Action] Executing 'book_ride' tool with destination: {destination}")
    return f"I have booked a ride to {destination}. The car should arrive in 5 minutes."

def tool_check_calendar():
    print("[Agent Action] Executing 'check_calendar' tool.")
    events = ["10 AM: Doctor's Appointment", "2 PM: Physical Therapy"]
    return f"Today, you have two events: {'; '.join(events)}."

def tool_toggle_device(device_name="the lights"):
    print(f"[Agent Action] Executing 'toggle_device' tool for: {device_name}")
    if device_name in smart_home_devices:
        current_state = smart_home_devices[device_name]
        new_state = "On" if current_state == "Off" else "Off"
        smart_home_devices[device_name] = new_state
        return f"I have turned the {device_name} {new_state}."
    return f"I couldn't find a device named {device_name}."

def tool_get_health_status():
    print("[Agent Action] Executing 'get_health' tool.")
    return f"Your current heart rate is {random.randint(68, 88)} bpm, which looks normal."

def tool_send_whatsapp(recipient="an unknown contact", message="a default message"):
    print(f"[Agent Action] Executing 'send_whatsapp' tool to {recipient}.")
    return f"OK, I've sent the message '{message}' to {recipient} on WhatsApp."

# ===============================================
# --- MAIN DATA GENERATION FUNCTION ---
# Used by Dashboard, Health, and Assistant pages.
# ===============================================
def get_simulated_data():
    """Generates a complete set of simulated data for all components."""
    heart_rate_history = [random.randint(68, 88) for _ in range(15)]
    data = {
        'connection_status': {
            'bluetooth': 'Connected' if random.choice([True, True, False]) else 'Disconnected',
            'wifi': 'Connected' if random.choice([True, True, True, False]) else 'Disconnected',
        },
        'health': {
            'heart_rate': heart_rate_history[-1],
            'oxygen_level': random.randint(95, 99),
            'history': heart_rate_history
        },
        'gait': {
            'speed': round(random.uniform(0.8, 1.2), 2),
            'step_length': random.randint(60, 75),
            'symmetry': round(random.uniform(0.95, 1.0), 2)
        },
        'smart_devices': smart_home_devices
    }
    return data

# ===============================================
# --- ROUTES FOR SERVING HTML PAGES ---
# These functions connect URLs to your HTML files.
# ===============================================
@app.route('/')
def home():
    """Serves the main Dashboard page."""
    return render_template('index.html')

@app.route('/location')
def location():
    """Serves the live Location/Navigation page."""
    return render_template('location.html')

@app.route('/health')
def health():
    """Serves the Health Analysis page."""
    return render_template('health.html')

@app.route('/assistant')
def assistant():
    """Serves the AI Assistant page."""
    return render_template('assistant.html')

# ===============================================
# --- API ENDPOINTS FOR FRONT-END INTERACTION ---
# These are the URLs your JavaScript calls to get or send data.
# ===============================================
@app.route('/api/data')
def api_data():
    """Provides general simulated data for the Dashboard, Health, and Assistant pages."""
    return jsonify(get_simulated_data())

@app.route('/api/sos_alert', methods=['POST'])
def sos_alert():
    """Handles the SOS button press from any page."""
    print("[ALERT] SOS button pressed! Simulating sending an emergency text.")
    return jsonify({"status": "success"}), 200

@app.route('/api/nearby_doctors')
def nearby_doctors():
    """Provides a simulated list of doctors for the Health page."""
    doctors = [{"name": "City General Hospital", "specialty": "Emergency Room", "distance": "1.2 km"},
               {"name": "Dr. Emily Carter", "specialty": "Cardiologist", "distance": "2.5 km"}]
    return jsonify(doctors)

@app.route('/api/toggle_device', methods=['POST'])
def toggle_device_api():
    """Handles the toggle switch for a smart home device on the Assistant page."""
    device_name = request.get_json().get('device')
    if device_name in smart_home_devices:
        smart_home_devices[device_name] = "On" if smart_home_devices[device_name] == "Off" else "Off"
        print(f"Toggled '{device_name}' to '{smart_home_devices[device_name]}'")
        return jsonify({"newState": smart_home_devices[device_name]})
    return jsonify({"error": "Device not found"}), 404

@app.route('/api/agent_command', methods=['POST'])
def agent_command():
    """Handles commands for the AI Agent and can trigger a navigation action."""
    user_message = request.get_json().get('message', '').lower()
    print(f"[User Command Received] '{user_message}'")

    nav_keywords = ['navigate to', 'find the location of', 'get directions to', 'take me to']
    if any(keyword in user_message for keyword in nav_keywords):
        destination = user_message
        for keyword in nav_keywords:
            destination = destination.replace(keyword, '').strip()
        print(f"[Agent Intent] Navigation recognized for destination: '{destination}'")
        return jsonify({
            "action": "navigate",
            "destination": destination,
            "displayText": f"Okay, calculating a route to {destination}..."
        })

    elif 'uber' in user_message or 'ride' in user_message:
        response_text = tool_book_ride("your home address")
    elif 'whatsapp' in user_message or 'send a message' in user_message:
        response_text = tool_send_whatsapp("your son", "Just checking in, everything is okay!")
    elif 'calendar' in user_message or 'plan' in user_message:
        response_text = tool_check_calendar()
    elif 'light' in user_message or 'lamp' in user_message:
        response_text = tool_toggle_device("Living Room Lamp")
    elif 'fan' in user_message:
        response_text = tool_toggle_device("Bedroom Fan")
    elif 'health' in user_message or 'heart rate' in user_message:
        response_text = tool_get_health_status()
    else:
        # Default assistant message (used if Groq isn't configured or fails)
        default_message = "I can help with navigation, booking rides, checking your schedule, your health, or controlling smart home devices."

        # Try Groq LLM for a conversational response (non-intrusive; only used when no explicit tool matched)
        groq_reply = call_groq_chat(user_message, system_prompt="You are a helpful assistant for a home/health/navigation app.")
        if groq_reply:
            response_text = groq_reply
        else:
            response_text = default_message

    print(f"[Agent Response] '{response_text}'")
    return jsonify({"response": response_text})

@app.route('/api/get_route', methods=['POST'])
def get_route():
    """Calculates a walking route for the Location page with improved validation, logging and fallback."""
    data = request.get_json(silent=True)
    if not data:
        print("[get_route] No JSON payload received.")
        return jsonify({"error": "No JSON payload received"}), 400

    # validate 'from' and 'to'
    from_coords = data.get('from')
    query = data.get('to')
    if not from_coords or 'lat' not in from_coords or 'lon' not in from_coords:
        print("[get_route] Invalid 'from' coordinates:", from_coords)
        return jsonify({"error": "Invalid 'from' coordinates. Expected {lat, lon}."}), 400
    if not query or (isinstance(query, str) and query.strip() == ""):
        print("[get_route] Missing or empty 'to' query:", query)
        return jsonify({"error": "Missing or empty 'to' field (destination string expected)."}), 400

    try:
        # Primary geocode attempt (bounded viewbox near user's location to prefer nearby matches)
        viewbox = f"{from_coords['lon']-0.1},{from_coords['lat']+0.1},{from_coords['lon']+0.1},{from_coords['lat']-0.1}"
        geocode_url_bounded = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(query)}&format=json&limit=1&viewbox={viewbox}"
        headers = {'User-Agent': 'GuardianApp/1.0'}
        print(f"[get_route] Geocode (bounded) URL: {geocode_url_bounded}")
        geocode_resp = requests.get(geocode_url_bounded, headers=headers, timeout=8)
        print("[get_route] Geocode (bounded) status:", geocode_resp.status_code)
        print("[get_route] Geocode (bounded) body:", geocode_resp.text[:1000])

        location = geocode_resp.json() if geocode_resp.status_code == 200 else []
        # Fallback: try an unbounded general search if bounded search found nothing
        if not location:
            geocode_url_general = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(query)}&format=json&limit=1"
            print(f"[get_route] Geocode fallback (general) URL: {geocode_url_general}")
            geocode_resp2 = requests.get(geocode_url_general, headers=headers, timeout=8)
            print("[get_route] Geocode (general) status:", geocode_resp2.status_code)
            print("[get_route] Geocode (general) body:", geocode_resp2.text[:1000])
            location = geocode_resp2.json() if geocode_resp2.status_code == 200 else []

        if not location:
            print("[get_route] Destination not found by Nominatim for query:", query)
            return jsonify({"error": "Destination not found by geocoding service."}), 404

        to_coords = {"lat": float(location[0]["lat"]), "lon": float(location[0]["lon"])}
        print(f"[get_route] Resolved to_coords: {to_coords}")

        # Call OSRM for walking route
        osrm_url = f"http://router.project-osrm.org/route/v1/walking/{from_coords['lon']},{from_coords['lat']};{to_coords['lon']},{to_coords['lat']}?overview=full&geometries=geojson&steps=true"
        print("[get_route] OSRM URL:", osrm_url)
        route_resp = requests.get(osrm_url, timeout=8)
        print("[get_route] OSRM status:", route_resp.status_code)
        print("[get_route] OSRM body (start):", route_resp.text[:1000])

        if route_resp.status_code != 200:
            print("[get_route] OSRM request failed", route_resp.status_code)
            return jsonify({"error": "Routing service unreachable or returned an error."}), 502

        route_json = route_resp.json()
        routes = route_json.get('routes') or []
        if not routes:
            print("[get_route] No routes returned by OSRM. Response:", route_json)
            return jsonify({"error": "No route found between points."}), 404

        route_data = routes[0]
        # Build human-readable steps
        steps = []
        legs = route_data.get('legs', [])
        if legs:
            for step in legs[0].get('steps', []):
                maneuver = step.get('maneuver', {})
                maneuver_type = maneuver.get('type', 'continue')
                modifier = maneuver.get('modifier', 'straight')
                street_name = step.get('name') or 'the road'
                if maneuver_type == 'depart':
                    instruction = f"Head toward {street_name}"
                elif maneuver_type == 'arrive':
                    instruction = f"You will arrive at your destination"
                else:
                    instruction = f"{maneuver_type.replace('_', ' ').capitalize()} {modifier} onto {street_name}"
                steps.append({"text": instruction, "location": maneuver.get('location')})
        else:
            print("[get_route] OSRM legs missing:", route_data)
            return jsonify({"error": "Routing data incomplete."}), 500

        return jsonify({"geometry": route_data.get('geometry'), "steps": steps})

    except requests.exceptions.Timeout:
        print("[get_route] External service timeout.")
        return jsonify({"error": "External service timeout. Try again later."}), 504
    except requests.exceptions.RequestException as e:
        print("[get_route] Requests exception:", e)
        return jsonify({"error": "Error connecting to external service."}), 502
    except Exception as e:
        print("[get_route] Unexpected error:", e)
        return jsonify({"error": "Internal server error."}), 500


# ===============================================
# --- This runs the Flask application ---
# ===============================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
