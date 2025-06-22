// ==========================================
// CONFIGURATION CONSTANTS
// ==========================================
const DEFAULT_HOST = 'http://localhost:7272';

// ==========================================
// GLOBAL STATE
// ==========================================
let settings;
let isLoading = false;
let articleIdCounter = 1;
let debugMode = false;
let sessionId = null;

// ==========================================
// DOM ELEMENTS
// ==========================================
const configBtn = document.getElementById('config-btn');
const configPanel = document.getElementById('config-panel');
const messagesContainer = document.getElementById('messages-container');
const userInput = document.getElementById('user-input');
const inputDiv = document.getElementById('input');
const inputHelp = document.getElementById('input-help');
const sendBtn = document.getElementById('send-btn');
const mainEl = document.querySelector('main');

// Configuration elements
const apiUrlInput = document.getElementById('api-url');
const modelSelect = document.getElementById('model');
const temperatureInput = document.getElementById('temperature');
const maxTokensInput = document.getElementById('max-tokens');
const debugModeCheckbox = document.getElementById('debug-mode');
const chunkLimitInput = document.getElementById('chunk-limit');
const searchStrategySelect = document.getElementById('search-strategy');
const includeWebSearchCheckbox = document.getElementById('include-web-search');
const feedbackUrlInput = document.getElementById('feedback-url');
const feedbackStatusEl = document.getElementById('feedback-status');

function detectEnvironment() {
  const hostname = window.location.hostname;
  return (!hostname || hostname === "doudou") ? "dev" : "prod";
}

function validateSettings(env) {
  if (!allSettings) {
    throw new Error("allSettings not found. Make sure settings.js is included before config.js.");
  }
  if (!allSettings.profiles) {
    throw new Error("allSettings.profiles not found. Invalid settings structure.");
  }
  if (!allSettings.profiles[env]) {
    throw new Error(`Settings inconnus pour '${env}'. Available profiles: ${Object.keys(allSettings.profiles).join(', ')}`);
  }
}

function initializeSettings() {
  try {
    const env = detectEnvironment();
    validateSettings(env);
    settings = allSettings.profiles[env];
    return true;
  } catch (err) {
    console.error("Settings initialization failed:", err.message);
    return false;
  }
}

function loadSettings() {
  try {
    if (!settings) throw new Error("Settings not loaded. Make sure settings.js is included before config.js.");
    applySettings(settings);
  } catch (err) {
    addMainError("Failed to load settings: " + err.message);
  }
}

function applySettings(settings) {
    // Set API URL
    if (settings.apiUrl && typeof apiUrlInput !== "undefined") {
        apiUrlInput.value = settings.apiUrl;
    }

    if (settings.feedbackUrl && typeof feedbackUrlInput !== "undefined") {
        feedbackUrlInput.value = settings.feedbackUrl;
    }

    // Populate language model select options
    if (settings.models && Array.isArray(settings.models) && typeof modelSelect !== "undefined") {
        modelSelect.innerHTML = '';

        // Build model options using the new structure
        settings.models.forEach(modelKey => {
            const modelConfig = allSettings.modelDefaults[modelKey];
            if (modelConfig) {
                const option = document.createElement('option');
                option.value = modelKey;
                option.textContent = modelConfig.label;
                if (modelConfig.selected) option.selected = true;
                if (modelConfig.disabled) option.disabled = true;
                modelSelect.appendChild(option);
            }
        });

        // Set debug mode from settings
        if (typeof debugModeCheckbox !== "undefined" && settings.debugMode !== undefined) {
        debugModeCheckbox.checked = settings.debugMode;
        debugMode = settings.debugMode;
        }

        // Initialize temperature and max tokens according to selected model
        if (typeof temperatureInput !== "undefined" && Array.isArray(settings.models)) {
        const selectedModelKey = modelSelect.value;
        const modelConfig = allSettings.modelDefaults[selectedModelKey];

        if (modelConfig && modelConfig.defaultTemperature !== undefined) {
            temperatureInput.value = modelConfig.defaultTemperature;
        }
        if (typeof maxTokensInput !== "undefined" && modelConfig && modelConfig.defaultMaxTokens !== undefined) {
            maxTokensInput.value = modelConfig.defaultMaxTokens;
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

        setModelTariffDisplay(selectedModelKey);
        }
    }
}

function setModelTariffDisplay(modelKey) {
    const fallback = "NA (unknown)";
    const loading = "...";

    const inputTariffEl = document.getElementById('input-tariff');
    const outputTariffEl = document.getElementById('output-tariff');

    const modelConfig = allSettings.modelDefaults[modelKey];
    const tariff = modelConfig?.tariff;

    if (tariff && inputTariffEl && outputTariffEl) {
        inputTariffEl.textContent = formatTariff(tariff.input, fallback);
        outputTariffEl.textContent = formatTariff(tariff.output, fallback);
    } else {
        if (inputTariffEl) inputTariffEl.textContent = loading;
        if (outputTariffEl) outputTariffEl.textContent = loading;
    }
}

function formatTariff(value, fallback) {
    return typeof value === "number" ? value.toFixed(2) : fallback;
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

    // Input text message handlers
    sendBtn.addEventListener('click', processInput);;

    userInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        // Don't add a new line
        e.preventDefault();
        // Process the message
        sendBtn.click();
    }
    });

    userInput.addEventListener('input', function() {
        // Auto-resize the input field
        this.style.height = 'auto';
        // But no more than 120px tall
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });

    // Update backend status display when URL changes
    apiUrlInput.addEventListener('change', updateStatusDisplay);

    // Set temperature and max-tokens to default values when model changes
    modelSelect.addEventListener('change', () => {
        const selectedModelKey = modelSelect.value;
        const modelConfig = allSettings.modelDefaults[selectedModelKey];

        if (modelConfig && modelConfig.defaultTemperature !== undefined) {
            temperatureInput.value = modelConfig.defaultTemperature;
        }
        if (modelConfig && modelConfig.defaultMaxTokens !== undefined) {
            maxTokensInput.value = modelConfig.defaultMaxTokens;
        }
        // Set model tariff display on model change
        setModelTariffDisplay(selectedModelKey);

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
        window.open(feedbackUrlInput.value.replace(/\/$/, '') + '/v1/analytics/view', '_blank');
    });

    document.getElementById('privacy-policy-link').addEventListener('click', function(e) {
        e.preventDefault();
        alert('Privacy policy coming soon!');
    });
}

function handleDebugModeToggle() {
    debugMode = debugModeCheckbox.checked;

    if (debugMode) {
        console.log('🐛 Debug mode enabled - API responses will be logged to console');
    } else {
        console.log('🐛 Debug mode disabled');
    }
    // Update stats visibility in the UI
    if (typeof updateStatsVisibility === "function") updateStatsVisibility();
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

function fetchFeedbackStatus() {
    if (!feedbackUrlInput || !feedbackStatusEl) return;
    const url = feedbackUrlInput.value.replace(/\/$/, '') + '/health';
    fetch(url)
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
// SESSION MANAGEMENT
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

// ==========================================
// INITIALIZATION
// ==========================================

async function initializeConfig() {
  // Initialize settings first
  if (!initializeSettings()) {
    addMainError("Settings initialization failed. Check console for details.");
    return;
  }
  // Load settings before anything else
  try {
    await loadSettings();
    setupEventListeners();

    // Lancement du polling toutes les secondes
    const POLL_INTERVAL_MS = 1000;
    setInterval(fetchApiStatus, POLL_INTERVAL_MS);
    setInterval(fetchFeedbackStatus, POLL_INTERVAL_MS);

    debugMode = debugModeCheckbox.checked;
    debugLog('Configuration initialized');
  } catch (err) {
    addMainError("Initialization failed: " + err.message);
    console.error('Initialization error:', err);
  }
}

if (document.readyState === 'loading') {
     document.addEventListener('DOMContentLoaded', initializeConfig);
} else {
    initializeConfig();
}
