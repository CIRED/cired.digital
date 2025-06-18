// ==========================================
// CONFIGURATION CONSTANTS
// ==========================================
const DEFAULT_HOST = 'http://localhost:7272';
const FEEDBACK_HOST = 'http://localhost:7275';

// ==========================================
// GLOBAL STATE
// ==========================================
let isLoading = false;
let messageIdCounter = 1;
let debugMode = false;
let sessionId = null;

// ==========================================
// DOM ELEMENTS
// ==========================================
const configBtn = document.getElementById('config-btn');
const configPanel = document.getElementById('config-panel');
const messagesContainer = document.getElementById('messages-container');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const errorContainer = document.getElementById('error-container');
const errorText = document.getElementById('error-text');

// Configuration elements
const apiUrlInput = document.getElementById('api-url');
const modelSelect = document.getElementById('model');
const temperatureInput = document.getElementById('temperature');
const maxTokensInput = document.getElementById('max-tokens');
const debugModeCheckbox = document.getElementById('debug-mode');
const chunkLimitInput = document.getElementById('chunk-limit');
const searchStrategySelect = document.getElementById('search-strategy');
const includeWebSearchCheckbox = document.getElementById('include-web-search');

// Status display elements (none at the moment)

// ==========================================
// SETTINGS LOADER
// ==========================================
const hostname = window.location.hostname;

const env = (!hostname || hostname === "doudou") ? "dev" : "prod";
if (!window.allSettings || !window.allSettings[env]) {
  throw new Error(`Settings inconnus pour '${env}'`);
}
window.Settings = window.allSettings[env];

function loadSettings() {
  try {
    if (!window.Settings) throw new Error("Settings not loaded. Make sure settings.js is included before config.js.");
    applySettings(window.Settings);
  } catch (err) {
    showError("Failed to load settings: " + err.message);
  }
}

function applySettings(settings) {
  // Set API URL
  if (settings.apiUrl && typeof apiUrlInput !== "undefined") {
    apiUrlInput.value = settings.apiUrl;
  }

  // Populate language model select options
  if (settings.models && Array.isArray(settings.models) && typeof modelSelect !== "undefined") {
    modelSelect.innerHTML = '';
    settings.models.forEach(model => {
      const option = document.createElement('option');
      option.value = model.value;
      option.textContent = model.label;
      if (model.selected) option.selected = true;
      if (model.disabled) option.disabled = true;
      modelSelect.appendChild(option);
    });
    // Set debug mode from settings
    if (typeof debugModeCheckbox !== "undefined" && settings.debugMode !== undefined) {
      debugModeCheckbox.checked = settings.debugMode;
      debugMode = settings.debugMode;
    }
    // Initialise la température et max tokens selon le modèle sélectionné
    if (typeof temperatureInput !== "undefined" && Array.isArray(settings.models)) {
      const sel = settings.models.find(m => m.value === modelSelect.value);
      if (sel && sel.defaultTemperature !== undefined) {
        temperatureInput.value = sel.defaultTemperature;
      }
      if (typeof maxTokensInput !== "undefined" && sel && sel.defaultMaxTokens !== undefined) {
        maxTokensInput.value = sel.defaultMaxTokens;
      }
      if (chunkLimitInput && settings.chunkLimit !== undefined) {
        chunkLimitInput.value = settings.chunkLimit;
      }
      if (searchStrategySelect && settings.searchStrategy !== undefined) {
        searchStrategySelect.value = settings.searchStrategy;
      }
      if (includeWebSearchCheckbox && settings.includeWebSearch !== undefined) {
        includeWebSearchCheckbox.checked = settings.includeWebSearch;
      }
    }
  }
}

// ==========================================
// EVENT LISTENERS SETUP
// ==========================================
function setupEventListeners() {
    // Configuration panel toggle
    configBtn.addEventListener('click', () => {
        configPanel.classList.toggle('hidden');
    });
    const configCloseBtn = document.getElementById('config-close-btn');
    if (configCloseBtn) {
        configCloseBtn.addEventListener('click', () => {
            configPanel.classList.add('hidden');
        });
    }

    // Send message handlers
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', handleKeyPress);

    // Auto-resize textarea
    messageInput.addEventListener('input', handleTextAreaResize);

    // Update status display when config changes
    // Met à jour le statut et la température à chaque changement d’URL ou de modèle
    apiUrlInput.addEventListener('change', updateStatusDisplay);
    modelSelect.addEventListener('change', () => {
        const sel = window.Settings.models.find(m => m.value === modelSelect.value);
        if (sel && sel.defaultTemperature !== undefined) {
            temperatureInput.value = sel.defaultTemperature;
        }
        if (sel && sel.defaultMaxTokens !== undefined) {
            maxTokensInput.value = sel.defaultMaxTokens;
        }
        updateStatusDisplay();
    });

    // Debug mode
    debugModeCheckbox.addEventListener('change', handleDebugModeToggle);
    if (chunkLimitInput) {
      chunkLimitInput.addEventListener('change', updateStatusDisplay);
    }
    if (searchStrategySelect) {
      searchStrategySelect.addEventListener('change', updateStatusDisplay);
    }
    if (includeWebSearchCheckbox) {
      includeWebSearchCheckbox.addEventListener('change', updateStatusDisplay);
    }

    initializePrivacyMode();
    initializeSession();

    document.getElementById('view-analytics-link').addEventListener('click', function(e) {
        e.preventDefault();
        window.open(FEEDBACK_HOST + '/v1/analytics/view', '_blank');
    });

    document.getElementById('privacy-policy-link').addEventListener('click', function(e) {
        e.preventDefault();
        alert('Privacy policy coming soon!');
    });
}

function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function handleTextAreaResize() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
}

function handleDebugModeToggle() {
    debugMode = debugModeCheckbox.checked;

    if (debugMode) {
        console.log('🐛 Debug mode enabled - API responses will be logged to console');
    } else {
        console.log('🐛 Debug mode disabled');
    }
}
// ==========================================
// UTILITY FUNCTIONS
// ==========================================
function updateStatusDisplay() {
    clearChunkCache();
    fetchApiStatus();
}

function fetchApiStatus() {
    const statusEl = document.getElementById('api-status');
    if (!statusEl) return;
    const url = apiUrlInput.value.replace(/\/$/, '') + '/v3/health';
    fetch(url)
        .then(res => res.json())
        .then(data => {
            const message = data.results?.message?.toUpperCase() || data.status || data.health || 'unknown';
            statusEl.textContent = `Server status: ${message}`;
            statusEl.className = 'status-text status-success';
        })
        .catch(() => {
            statusEl.textContent = 'Server status: unreachable';
            statusEl.className = 'status-text status-error';
        });
}


function debugLog(message, data = null) {
    if (debugMode) {
        if (data) {
            console.log(`🐛 ${message}`, data);
        } else {
            console.log(`🐛 ${message}`);
        }
    }
}

// ==========================================
// ERROR HANDLING
// ==========================================
function showError(message) {
    errorText.textContent = message;
    errorContainer.classList.remove('hidden');
    errorContainer.classList.add('flex');
}

function hideError() {
    errorContainer.classList.add('hidden');
    errorContainer.classList.remove('flex');
}
// ==========================================
// PRIVACY MODE FUNCTIONALITY
// ==========================================
function initializePrivacyMode() {
    debugLog('Initializing privacy mode');

    const privacyCheckbox = document.getElementById('privacy-mode');
    const statusText = document.getElementById('status-text');

    const privacyMode = localStorage.getItem('privacy-mode') === 'true';
    privacyCheckbox.checked = privacyMode;

    debugLog('Privacy mode state loaded', { privacyMode });

    updatePrivacyStatus();

    privacyCheckbox.addEventListener('change', function() {
        localStorage.setItem('privacy-mode', this.checked);
        debugLog('Privacy mode toggled', { enabled: this.checked });
        updatePrivacyStatus();
    });
}

function updatePrivacyStatus() {
    const privacyMode = localStorage.getItem('privacy-mode') === 'true';
    debugLog('Privacy status updated', { privacyMode });
}

function isPrivacyModeEnabled() {
    return localStorage.getItem('privacy-mode') === 'true';
}

// ==========================================
// ==========================================
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

function initializeSession() {
    sessionId = localStorage.getItem('session-id');
    if (!sessionId) {
        sessionId = generateSessionId();
        localStorage.setItem('session-id', sessionId);
    }

    logSessionStart();
}

async function logSessionStart() {
    try {
        const privacyMode = isPrivacyModeEnabled();

        const sessionData = {
            session_id: sessionId,
            start_time: new Date().toISOString(),
            privacy_mode: privacyMode
        };

        const response = await fetch(`${FEEDBACK_HOST}/v1/log/session`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(sessionData)
        });

        if (response.ok) {
            debugLog('Session logged successfully');
        } else {
            console.warn('Session logging failed:', response.status);
        }
    } catch (error) {
        console.error('Error logging session:', error);
    }
}

async function logQuery(queryId, question, queryParameters) {
    try {
        const privacyMode = isPrivacyModeEnabled();

        const queryData = {
            session_id: sessionId,
            query_id: queryId,
            question: question,
            query_parameters: queryParameters,
            timestamp: new Date().toISOString(),
            privacy_mode: privacyMode
        };

        const response = await fetch(`${FEEDBACK_HOST}/v1/log/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(queryData)
        });

        if (response.ok) {
            debugLog('Query logged successfully');
        } else {
            console.warn('Query logging failed:', response.status);
        }
    } catch (error) {
        console.error('Error logging query:', error);
    }
}

async function logResponse(queryId, response, processingTime) {
    try {
        const privacyMode = isPrivacyModeEnabled();

        const responseData = {
            query_id: queryId,
            response: response,
            processing_time: processingTime,
            timestamp: new Date().toISOString(),
            privacy_mode: privacyMode
        };

        const responseResult = await fetch(`${FEEDBACK_HOST}/v1/log/response`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(responseData)
        });

        if (responseResult.ok) {
            debugLog('Response logged successfully');
        } else {
            console.warn('Response logging failed:', responseResult.status);
        }
    } catch (error) {
        console.error('Error logging response:', error);
    }
}


// ==========================================
// INITIALIZATION
// ==========================================

async function initializeConfig() {
  // Load settings before anything else
  try {
    await loadSettings();
    updateStatusDisplay();
    setupEventListeners();
    debugMode = debugModeCheckbox.checked;
    debugLog('Configuration initialized');
  } catch (err) {
    showError("Initialization failed: " + err.message);
    console.error('Initialization error:', err);
  }
}


if (document.readyState === 'loading') {
     document.addEventListener('DOMContentLoaded', initializeConfig);
} else {
    initializeConfig();
}
