// Status.js

const backendStatusIndicator = document.getElementById('backend-status-indicator');
const modelStatusIndicator = document.getElementById('model-status-indicator');
const monitorStatusIndicator = document.getElementById('monitor-status-indicator');

const apiUrlHealthEndpoint = apiUrlInput.value.replace(/\/$/, '') + '/v3/health';
const monitorUrlHealthEndpoint = feedbackUrlInput.value.replace(/\/$/, '') + '/health';


function updateStatusDisplay() {
    clearChunkCache();
    fetchApiStatus();
}

function fetchApiStatus() {
    if (!apiStatusElement) return;
    fetch(apiUrlHealthEndpoint)
        .then(res => res.json())
        .then(data => {
            const message = data.results?.message?.toUpperCase() || data.status || data.health || 'unknown';
            apiStatusElement.textContent = `Server status: ${message}`;
            apiStatusElement.className = 'status-text status-success';
        })
        .catch(() => {
            apiStatusElement.textContent = 'Server status: unreachable';
            apiStatusElement.className = 'status-text status-error';
        });
}

function fetchMonitorStatus() {
    if (!feedbackUrlInput || !feedbackStatusEl) return;
    fetch(monitorUrlHealthEndpoint)
        .then(res => res.json())
        .then(data => {
            const s = (data.status || 'unknown').toUpperCase();
            feedbackStatusEl.textContent = `Server status : ${s}`;
            feedbackStatusEl.className = s === 'OK' ? 'status-text status-success' : 'status-text status-error';
        })
        .catch(() => {
            feedbackStatusEl.textContent = 'Server status : Unreachable';
            feedbackStatusEl.className = 'status-text status-error';
        });
}
