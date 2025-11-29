document.addEventListener('DOMContentLoaded', function() {
    console.log("Assistant script loaded and running.");

    // --- Element References ---
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatBox = document.getElementById('chat-box');
    const suggestionChipsContainer = document.getElementById('suggestion-chips');
    const sosButton = document.getElementById('sos-button');

    // --- Event Listeners ---
    chatForm.addEventListener('submit', handleChatSubmit);

    suggestionChipsContainer.addEventListener('click', (event) => {
        if (event.target.classList.contains('chip')) {
            chatInput.value = event.target.textContent;
            chatForm.dispatchEvent(new Event('submit', { cancelable: true }));
        }
    });

    if (sosButton) {
        sosButton.addEventListener('click', () => {
            if (confirm("Are you sure you want to send an emergency alert?")) {
                alert("Emergency alert sent!");
                fetch('/api/sos_alert', { method: 'POST' });
            }
        });
    }

    // --- Main Chat Handler ---
    function handleChatSubmit(event) {
        event.preventDefault(); // Prevent page reload
        const userMessage = chatInput.value.trim();
        if (userMessage === '') return;
        displayMessage(userMessage, 'user');
        chatInput.value = '';
        getAgentResponse(userMessage);
    }

    // --- Get Agent Response (Handles Special Actions) ---
    function getAgentResponse(message) {
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'ai-message';
        typingIndicator.id = 'typing-indicator';
        typingIndicator.innerHTML = `<i class="fa-solid fa-robot"></i><div class="typing-dots"><span></span><span></span><span></span></div>`;
        chatBox.appendChild(typingIndicator);
        chatBox.scrollTop = chatBox.scrollHeight;

        fetch('/api/agent_command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            typingIndicator.remove();

            // Check if the backend sent a special "action" command
            if (data.action === 'navigate') {
                displayMessage(data.displayText, 'ai'); // Show the confirmation text
                
                // Wait a moment for the user to read, then redirect
                setTimeout(() => {
                    const destination = encodeURIComponent(data.destination);
                    window.location.href = `/location?destination=${destination}`;
                }, 2000);

            } else if (data.response) {
                // If it's a normal response, display the text
                displayMessage(data.response, 'ai');
                // Refresh the sidebar in case a smart home device was toggled
                updateSidebarCards();
            } else {
                // Fallback for any unexpected response
                console.error("Received an unknown response format from the server:", data);
                displayMessage("Sorry, I encountered an error.", 'ai');
            }
        });
    }

    // --- Display Messages in Chat Box ---
    function displayMessage(message, sender) {
        const messageWrapper = document.createElement('div');
        messageWrapper.className = sender === 'user' ? 'user-message' : 'ai-message';
        const iconClass = sender === 'user' ? 'fa-user' : 'fa-robot';
        messageWrapper.innerHTML = `<i class="fa-solid ${iconClass}"></i><p>${message}</p>`;
        chatBox.appendChild(messageWrapper);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // --- Sidebar Cards Logic ---
    function updateSidebarCards() {
        fetch('/api/data')
            .then(response => response.json())
            .then(data => {
                // Update Connectivity Status
                updateStatusElement('bluetooth', data.connection_status.bluetooth);
                updateStatusElement('wifi', data.connection_status.wifi);
                updateStatusElement('gps', navigator.geolocation ? 'Connected' : 'Unsupported');

                // Update Smart Home Devices list
                const deviceList = document.getElementById('device-list');
                deviceList.innerHTML = ''; // Clear previous list
                for (const deviceName in data.smart_devices) {
                    const state = data.smart_devices[deviceName];
                    const li = document.createElement('li');
                    li.innerHTML = `
                        <span>${deviceName}</span>
                        <div class="device-status">
                            <span class="status-text">${state}</span>
                            <label class="switch">
                                <input type="checkbox" ${state === 'On' ? 'checked' : ''} data-device="${deviceName}">
                                <span class="slider"></span>
                            </label>
                        </div>
                    `;
                    deviceList.appendChild(li);
                }
                
                document.querySelectorAll('.switch input').forEach(toggle => {
                    toggle.addEventListener('change', handleDeviceToggle);
                });
            });
    }

    function handleDeviceToggle(event) {
        const deviceName = event.target.dataset.device;
        fetch('/api/toggle_device', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device: deviceName })
        })
        .then(() => {
            // Refresh the sidebar to show the new state from the server
            updateSidebarCards();
        });
    }

    function updateStatusElement(id, status) {
        const iconEl = document.getElementById(`${id}-icon`);
        const textEl = document.getElementById(`${id}-status`);
        if (!iconEl || !textEl) return;
        
        textEl.textContent = status;
        iconEl.style.color = (status === 'Connected') ? 'var(--success-color)' : 'var(--danger-color)';
    }
    
    // --- Initial and Periodic Updates ---
    updateSidebarCards();
    setInterval(updateSidebarCards, 5000);
});