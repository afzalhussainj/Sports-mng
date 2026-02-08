"""
JavaScript utilities and WebSocket handlers
"""

// Global WebSocket connection
let dashboardSocket = null;

function connectDashboardSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    dashboardSocket = new WebSocket(`${protocol}//${window.location.host}/ws/dashboard/`);
    
    dashboardSocket.onopen = function(e) {
        console.log('Dashboard WebSocket connected');
    };
    
    dashboardSocket.onclose = function(e) {
        console.log('Dashboard WebSocket closed');
        // Attempt to reconnect after 3 seconds
        setTimeout(connectDashboardSocket, 3000);
    };
    
    dashboardSocket.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
}

// Initialize WebSocket on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', connectDashboardSocket);
} else {
    connectDashboardSocket();
}
