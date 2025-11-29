document.addEventListener('DOMContentLoaded', function() {
    // --- Map and Path Initialization ---
    const map = L.map('map').setView([51.505, -0.09], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    let userMarker = L.marker([0,0]).addTo(map);
    let userPathPolyline = L.polyline([], { color: '#4A90E2', weight: 5 }).addTo(map);
    let routePolyline = L.polyline([], { color: '#E35050', weight: 6, dashArray: '5, 10' }).addTo(map);

    // --- State Variables ---
    let userCurrentPosition = null;
    let startTime = null;
    let totalDistance = 0;
    let routeSteps = [];
    let currentStepIndex = -1;

    // --- Element References ---
    const getRouteBtn = document.getElementById('get-route-btn');
    const destinationInput = document.getElementById('destination-input');
    const instructionPanel = document.getElementById('instruction-panel');
    const instructionText = document.getElementById('instruction-text');
    const prevStepBtn = document.getElementById('prev-step-btn');
    const nextStepBtn = document.getElementById('next-step-btn');
    const sosButton = document.getElementById('sos-button');

    // --- Auto-Navigation Function ---
    function checkForAutoNavigation() {
        console.log("Checking for auto-navigation command...");
        const params = new URLSearchParams(window.location.search);
        const destination = params.get('destination');

        if (destination) {
            console.log(`Destination found in URL: ${destination}`);
            destinationInput.value = decodeURIComponent(destination);

            const gpsCheckInterval = setInterval(() => {
                if (userCurrentPosition) {
                    console.log("GPS lock acquired. Automatically finding route.");
                    clearInterval(gpsCheckInterval);
                    getRouteBtn.click(); // Programmatically click the "Find Route" button
                } else {
                    console.log("Waiting for GPS lock...");
                }
            }, 1000);
        }
    }

    // --- Event Listeners ---
    getRouteBtn.addEventListener('click', findAndDisplayRoute);
    prevStepBtn.addEventListener('click', () => displayStep(currentStepIndex - 1));
    nextStepBtn.addEventListener('click', () => displayStep(currentStepIndex + 1));
    if (sosButton) {
        sosButton.addEventListener('click', () => {
            if (confirm("Are you sure you want to send an emergency alert?")) {
                alert("Emergency alert sent!");
                fetch('/api/sos_alert', { method: 'POST' });
            }
        });
    }

    // --- Activate Live GPS ---
    if ('geolocation' in navigator) {
        navigator.geolocation.watchPosition(handleGpsUpdate, handleGpsError, { enableHighAccuracy: true });
    } else {
        alert("Your browser does not support Geolocation.");
    }

    // --- Main Functions ---
    function handleGpsUpdate(position) {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        userCurrentPosition = { lat, lon };
        const newLatLng = L.latLng(lat, lon);

        if (!startTime) {
            startTime = new Date();
            map.setView(newLatLng, 17);
            userMarker.setLatLng(newLatLng).bindPopup('Your Location').openPopup();
        }

        if(userPathPolyline.getLatLngs().length > 0) {
            totalDistance += userPathPolyline.getLatLngs().slice(-1)[0].distanceTo(newLatLng);
        }
        userMarker.setLatLng(newLatLng);
        userPathPolyline.addLatLng(newLatLng);
        updateStats();
    }
    
    function handleGpsError(error) {
        console.error("Geolocation Error:", error.message);
        alert("Could not get your location. Please ensure location services are enabled.");
    }

    function findAndDisplayRoute() {
        const destination = destinationInput.value;
        if (!destination) {
            alert("Please enter a destination.");
            return;
        }
        if (!userCurrentPosition) {
            alert("Cannot get route. Your current location is not available yet.");
            return;
        }

        getRouteBtn.textContent = 'Calculating...';
        getRouteBtn.disabled = true;

        fetch('/api/get_route', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ from: userCurrentPosition, to: destination })
        })
        .then(response => response.ok ? response.json() : Promise.reject('Route not found'))
        .then(data => {
            const latLngs = data.geometry.coordinates.map(coord => [coord[1], coord[0]]);
            routePolyline.setLatLngs(latLngs);
            map.fitBounds(routePolyline.getBounds().pad(0.1));

            routeSteps = data.steps;
            currentStepIndex = -1;
            instructionPanel.style.display = 'flex';
            displayStep(0);
        })
        .catch(error => {
            console.error("Routing error:", error);
            alert("Could not calculate a route. Please try another search.");
            instructionPanel.style.display = 'none';
        })
        .finally(() => {
            getRouteBtn.textContent = 'Find Route';
            getRouteBtn.disabled = false;
        });
    }

    function displayStep(index) {
        if (index < 0 || index >= routeSteps.length) return;
        
        currentStepIndex = index;
        const step = routeSteps[index];
        instructionText.textContent = step.text;
        speakInstruction(step.text);

        const stepLocation = [step.location[1], step.location[0]];
        map.panTo(stepLocation, { animate: true });
    }
    
    function speakInstruction(text) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'en-US';
        utterance.rate = 1.0;
        window.speechSynthesis.speak(utterance);
    }
    
    function updateStats() {
        document.getElementById('distance-traveled').textContent = (totalDistance / 1000).toFixed(2) + ' km';
        const now = new Date();
        if (startTime) {
            const diffSeconds = Math.round((now - startTime) / 1000);
            const minutes = Math.floor(diffSeconds / 60).toString().padStart(2, '0');
            const seconds = (diffSeconds % 60).toString().padStart(2, '0');
            document.getElementById('duration').textContent = `${minutes}:${seconds}`;

            if (diffSeconds > 0) {
                const speedKph = ((totalDistance / diffSeconds) * 3.6).toFixed(1);
                document.getElementById('avg-speed').textContent = speedKph + ' km/h';
            }
        }
    }

    // --- Start the App ---
    checkForAutoNavigation();
});