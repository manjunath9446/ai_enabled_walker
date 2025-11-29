document.addEventListener('DOMContentLoaded', function() {
    console.log("Dynamic script loaded. Fetching data...");

    // Only run the live data fetching if we are not on the assistant page
    if (!window.location.pathname.endsWith('/assistant')) {
        // Fetch data immediately on page load
        fetchDataAndUpdate();
        // Then, fetch new data every 3 seconds (3000 milliseconds)
        setInterval(fetchDataAndUpdate, 3000);
    }

    // --- Main function to get data from our Python backend ---
    function fetchDataAndUpdate() {
        fetch('/api/data') // This sends a request to our app.py's "/api/data" route
            .then(response => response.json()) // Converts the response to a format JS can use
            .then(data => {
                // Once we have the data, we update the HTML
                console.log(data); // You can see the simulated data in the browser console
                updateDashboard(data);
                updateLocationPage(data);
                updateHealthPage(data);
            })
            .catch(error => console.error('Error fetching data:', error));
    }

    // --- Functions to update specific parts of the page ---
    function updateDashboard(data) {
        const bluetoothStatus = document.getElementById('bluetooth-status');
        const wifiStatus = document.getElementById('wifi-status');
        const heartRate = document.getElementById('heart-rate');
        const oxygenLevel = document.getElementById('oxygen-level');
        const fallAlert = document.getElementById('fall-alert');

        // Update connection status text and dot style
        if (bluetoothStatus) {
            bluetoothStatus.textContent = data.connection_status.bluetooth;
            bluetoothStatus.className = 'status-dot-' + data.connection_status.bluetooth.toLowerCase();
        }
        if (wifiStatus) {
            wifiStatus.textContent = data.connection_status.wifi;
            wifiStatus.className = 'status-dot-' + data.connection_status.wifi.toLowerCase();
        }

        // Update health numbers
        if (heartRate) heartRate.textContent = data.health.heart_rate;
        if (oxygenLevel) oxygenLevel.textContent = data.health.oxygen_level;

        // Show or hide the fall alert
        if (fallAlert) {
            fallAlert.style.display = data.fall_detected ? 'block' : 'none';
        }
    }

    function updateLocationPage(data) {
        const latitude = document.getElementById('latitude');
        const longitude = document.getElementById('longitude');
        if (latitude) latitude.textContent = data.gps.latitude;
        if (longitude) longitude.textContent = data.gps.longitude;
    }

    function updateHealthPage(data) {
        const gaitSpeed = document.getElementById('gait-speed');
        const gaitLength = document.getElementById('gait-length');
        const gaitSymmetry = document.getElementById('gait-symmetry');
        if (gaitSpeed) gaitSpeed.textContent = data.gait.speed;
        if (gaitLength) gaitLength.textContent = data.gait.step_length;
        if (gaitSymmetry) gaitSymmetry.textContent = data.gait.symmetry;
    }
});