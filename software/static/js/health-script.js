document.addEventListener('DOMContentLoaded', function() {
    // --- Chart.js Initialization ---
    const ctx = document.getElementById('healthChart').getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(74, 144, 226, 0.4)');
    gradient.addColorStop(1, 'rgba(74, 144, 226, 0)');

    const healthChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array(15).fill(''),
            datasets: [{
                label: 'Heart Rate',
                data: Array(15).fill(null),
                borderColor: '#4A90E2',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                backgroundColor: gradient,
                pointBackgroundColor: '#4A90E2',
                pointRadius: 0,
                pointHoverRadius: 6,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { suggestedMin: 50, suggestedMax: 100 }, x: { grid: { display: false }}},
            plugins: { legend: { display: false }}
        }
    });

    // --- Data Fetching and UI Updates ---
    function updateHealthData() {
        fetch('/api/data')
            .then(response => response.json())
            .then(data => {
                // Update stats and chart
                document.getElementById('heart-rate').textContent = data.health.heart_rate;
                document.getElementById('oxygen-level').textContent = data.health.oxygen_level;
                document.getElementById('gait-speed').textContent = data.gait.speed;
                document.getElementById('gait-length').textContent = data.gait.step_length;
                document.getElementById('gait-symmetry').textContent = data.gait.symmetry;

                healthChart.data.datasets[0].data = data.health.history;
                healthChart.data.labels = data.health.history.map((_, i) => `-${(data.health.history.length - i - 1) * 3}s`);
                healthChart.update();
            });
    }

    // --- Load Emergency Doctor Information ---
    function loadEmergencyContacts() {
        fetch('/api/nearby_doctors')
            .then(response => response.json())
            .then(doctors => {
                const doctorList = document.getElementById('doctor-list');
                doctorList.innerHTML = ''; // Clear "Loading..."

                doctors.forEach(doctor => {
                    const li = document.createElement('li');
                    li.innerHTML = `
                        <div class="doctor-info">
                            <strong>${doctor.name}</strong>
                            <span>${doctor.specialty} - ${doctor.distance} away</span>
                        </div>
                        <button class="action-button">Contact</button>
                    `;
                    li.querySelector('.action-button').addEventListener('click', () => {
                        alert(`SMART AUTOMATION:\n\nInitiating contact with ${doctor.name}.\nIn a real app, this could:\n- Call their number directly.\n- Book an Uber to their location.\n- Send your health data to them.`);
                    });
                    doctorList.appendChild(li);
                });
            });
    }

    // --- Start all processes ---
    updateHealthData();
    setInterval(updateHealthData, 3000);
    loadEmergencyContacts();

    // Make the generic SOS button work
    const sosButton = document.getElementById('sos-button');
    if (sosButton) {
        sosButton.addEventListener('click', () => {
            if (confirm("Are you sure you want to send an emergency alert?")) {
                alert("Emergency alert sent!");
                fetch('/api/sos_alert', { method: 'POST' });
            }
        });
    }
});