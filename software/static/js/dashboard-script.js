document.addEventListener('DOMContentLoaded', function() {
    // --- Global variables ---
    let map, marker, userCurrentPosition;

    // --- Initialize the App ---
    initializeMap();
    setupEventListeners();
    startDataFetching();
    activateLiveGps();

    // --- Setup Functions ---
    function initializeMap() {
        map = L.map('map').setView([51.505, -0.09], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
             attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        marker = L.marker([51.505, -0.09]).addTo(map).bindPopup('Your Location');
    }

    function setupEventListeners() {
        document.getElementById('sos-button').addEventListener('click', sendSosAlert);
        document.getElementById('recenter-button').addEventListener('click', recenterMap);
    }

    function startDataFetching() {
        fetchSimulatedData();
        setInterval(fetchSimulatedData, 3000);
    }

    // --- Core Logic ---
    function fetchSimulatedData() {
        fetch('/api/data')
            .then(response => response.json())
            .then(data => {
                updateHealthCard(data.health);
                updateStatusElement('bluetooth-status', data.connection_status.bluetooth);
                updateStatusElement('wifi-status', data.connection_status.wifi);
                updateOverallStatus(data);
            });
    }

    function activateLiveGps() {
        if ('geolocation' in navigator) {
            navigator.geolocation.watchPosition(
                (position) => {
                    userCurrentPosition = [position.coords.latitude, position.coords.longitude];
                    updateStatusElement('gps-status', 'Connected');
                    if (map) {
                        map.setView(userCurrentPosition, 16);
                        marker.setLatLng(userCurrentPosition);
                    }
                },
                () => {
                    updateStatusElement('gps-status', 'Error');
                }
            );
        } else {
            updateStatusElement('gps-status', 'Unsupported');
        }
    }
    
    // --- UI Update Functions ---
    function updateOverallStatus(data) {
        const statusCard = document.getElementById('status-card');
        const statusText = document.getElementById('status-text');
        const statusSubtext = document.getElementById('status-subtext');

        if (data.connection_status && Object.values(data.connection_status).includes('Disconnected')) {
            statusCard.className = 'card status-card-alert';
            statusText.textContent = 'Connection Issue';
            statusSubtext.textContent = 'One or more devices are disconnected.';
        } else {
            statusCard.className = 'card status-card-ok';
            statusText.textContent = 'All Systems Normal';
            statusSubtext.textContent = 'Monitoring your health and location.';
        }
    }

    function updateHealthCard(healthData) {
        if(healthData) {
            document.getElementById('heart-rate').textContent = healthData.heart_rate;
            document.getElementById('oxygen-level').textContent = healthData.oxygen_level;
        }
    }

    function updateStatusElement(elementId, status) {
        const el = document.getElementById(elementId);
        if(el) {
            const dot = el.previousElementSibling;
            el.textContent = status;
            if (status === 'Connected') {
                dot.classList.add('connected');
            } else {
                dot.classList.remove('connected');
            }
        }
    }

    // --- Action Functions ---
    function recenterMap() {
        if (userCurrentPosition) {
            map.setView(userCurrentPosition, 16);
        } else {
            alert("Still trying to find your location. Please wait.");
        }
    }

    function sendSosAlert() {
        const isConfirmed = confirm("Are you sure you want to send an emergency alert?");
        if (isConfirmed) {
            alert("Emergency alert sent! Your emergency contacts are being notified.");
            fetch('/api/sos_alert', { method: 'POST' });
        }
    }
});