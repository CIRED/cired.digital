// Status.js

let isBackendOK = false;

const backendStatusIndicator = document.getElementById('backend-status-indicator');
const modelStatusIndicator = document.getElementById('model-status-indicator');
const monitorStatusIndicator = document.getElementById('monitor-status-indicator');


function updateStatusDisplay() {
    clearChunkCache();
    fetchApiStatus();
}

function fetchApiStatus() {
    if (!apiStatusElement) return;
    const r2rURLHealthEndpoint = r2rURLInput.value.replace(/\/$/, '') + '/v3/health';
    fetch(r2rURLHealthEndpoint)
        .then(res => res.json())
        .then(data => {
            const message = data.results?.message?.toUpperCase() || data.status || data.health || 'unknown';
            apiStatusElement.textContent = `Server status: ${message}`;
            apiStatusElement.className = 'status-text status-success';

            const wasBackendOK = isBackendOK;
            isBackendOK = true;

            if (!wasBackendOK && isBackendOK) {
                refreshModels();
            }
        })
        .catch(() => {
            apiStatusElement.textContent = 'Server status: unreachable';
            apiStatusElement.className = 'status-text status-error';
            isBackendOK = false;
        });
}

function fetchMonitorStatus() {
    if (!cirdiURLInput || !feedbackStatusEl) return;
    const monitorUrlHealthEndpoint = cirdiURLInput.value.replace(/\/$/, '') + '/health';
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

async function refreshModels() {
    if (!modelStatusElement || !refreshModelsBtn) return;

    refreshModelsBtn.disabled = true;

    if (!isBackendOK) {
        modelStatusElement.textContent = 'Waiting for server';
        modelStatusElement.className = 'status-text';
        refreshModelsBtn.disabled = false;
        return;
    }

    modelStatusElement.textContent = 'Testing model...';
    modelStatusElement.className = 'status-text';

    try {
        const config = getConfiguration();
        const r2rURL = config.r2rURL;
        const selectedModel = config.model;

        const requestBody = {
            messages: [
                {"role": "system", "content": "Just reply with 'OK', this is a handshake test."},
                {"role": "user", "content": "Are you up?"}
            ],
            generation_config: {
                model: selectedModel,
                temperature: 0,
                max_tokens: 10,
                stream: false
            }
        };

        const response = await fetch(`${r2rURL}/v3/retrieval/completion`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (response.ok) {
            const data = await response.json();
            modelStatusElement.textContent = `Model: ${selectedModel} - OK`;
            modelStatusElement.className = 'status-text status-success';
        } else {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

    } catch (error) {
        modelStatusElement.textContent = `Model: ${modelSelect.value} - Error: ${error.message}`;
        modelStatusElement.className = 'status-text status-error';
        console.error('Model refresh failed:', error);
    } finally {
        refreshModelsBtn.disabled = false;
    }
}
