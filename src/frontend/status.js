// Status.js

let isBackendOK = false;

const backendStatusIndicator = document.getElementById('backend-status-indicator');
const modelStatusIndicator = document.getElementById('model-status-indicator');
const monitorStatusIndicator = document.getElementById('monitor-status-indicator');


function updateStatusDisplay() {
    clearChunkCache();
    updateR2RServerStatus();
}

function updateR2RServerStatus() {
    apiStatusElement = document.getElementById('r2r-server-status');
    r2rURLInput = document.getElementById('r2r-url');
    if (!apiStatusElement || !r2rURLInput) return;
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
                updateModelStatus();
            }
        })
        .catch(() => {
            apiStatusElement.textContent = 'Server status: unreachable';
            apiStatusElement.className = 'status-text status-error';
            isBackendOK = false;
        });
}

function updateCirdiServerStatus() {
    cirdiURLInput = document.getElementById('cirdi-url');
    cirdiServerStatusEl = document.getElementById('cirdi-server-status');
    if (!cirdiURLInput || !cirdiServerStatusEl) return;
    const monitorUrlHealthEndpoint = cirdiURLInput.value.replace(/\/$/, '') + '/health';
    fetch(monitorUrlHealthEndpoint)
        .then(res => res.json())
        .then(data => {
            const s = (data.status || 'unknown').toUpperCase();
            cirdiServerStatusEl.textContent = `Server status : ${s}`;
            cirdiServerStatusEl.className = s === 'OK' ? 'status-text status-success' : 'status-text status-error';
        })
        .catch(() => {
            cirdiServerStatusEl.textContent = 'Server status : Unreachable';
            cirdiServerStatusEl.className = 'status-text status-error';
        });
}

function setLLMStatus(status, message = '') {
    const modelStatusElement = document.getElementById('model-status');
    const updateModelStatusBtn = document.getElementById('refresh-models-btn');
    if (!modelStatusElement || !updateModelStatusBtn) return;

    updateModelStatusBtn.disabled = false;
    modelStatusElement.className = 'status-text';

    switch (status) {
        case 'waiting':
            modelStatusElement.textContent = 'R2R server not available...';
            modelStatusElement.className += ' status-error';
            break;
        case 'testing':
            modelStatusElement.textContent = 'Asking the model if it is up.';
            updateModelStatusBtn.disabled = true;
            break;
        case 'error':
            modelStatusElement.textContent = message;
            modelStatusElement.className += ' status-error';
            break;
        case 'success':
            modelStatusElement.textContent = message || 'Model status : OK';
            modelStatusElement.className += ' status-success';
            break;
        default:
            modelStatusElement.textContent = 'Model status : Unknown';
            modelStatusElement.className += ' status-error';
    }
}

async function updateModelStatus() {
    const modelStatusElement = document.getElementById('model-status');
    const updateModelStatusBtn = document.getElementById('refresh-models-btn');
    if (!modelStatusElement || !updateModelStatusBtn) return;

    if (!isBackendOK) {
        setLLMStatus('waiting');
        return;
    }

    setLLMStatus('testing');

    try {
        const r2rURLInput = document.getElementById('r2r-url');
        const modelSelect = document.getElementById('model-select');
        const selectedModel = modelSelect.value;
        if (!r2rURLInput || !modelSelect || !selectedModel) {
            throw new Error('Required form elements not found');
        }

        const endpoint = r2rURLInput.value.replace(/\/$/, '') + '/v3/retrieval/completion';
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

        debugLog(`Sending ${selectedModel} request:`, requestBody);
        const startTime = performance.now();
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(requestBody)
        });

        const endTime = performance.now();
        const elapsedSeconds = ((endTime - startTime) / 1000).toFixed(1);

        debugLog('LLM test response:', {
            status: response.status,
            ok: response.ok,
            elapsed: `${elapsedSeconds}s`
        });

        if (response.ok) {
            setLLMStatus('success', `${selectedModel} response time ${elapsedSeconds}s`);
        } else {
            // Try to parse as JSON first, fall back to text
            let errorMessage;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail?.message || errorData.message || `HTTP ${response.status}`;
            } catch {
                errorMessage = await response.text() || `HTTP ${response.status}`;
            }
            setLLMStatus('error', `${selectedModel} ${errorMessage}`);
        }
    } catch (error) {
        setLLMStatus('error', error.message);
    }
}
