// ==========================================
// CONFIGURATION CONSTANTS
// ==========================================
const DEFAULT_HOST = 'http://cired.digital:7272';
const FEEDBACK_HOST = 'http://cired.digital:7275';

// ==========================================
// GLOBAL STATE
// ==========================================
let isLoading = false;
let messageIdCounter = 1;
let debugMode = false;

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

// Status display elements
const apiUrlDisplay = document.getElementById('api-url-display');
const modelDisplay = document.getElementById('model-display');

// ==========================================
// EVENT LISTENERS SETUP
// ==========================================
function setupEventListeners() {
    // Configuration panel toggle
    configBtn.addEventListener('click', () => {
        configPanel.classList.toggle('hidden');
    });

    // Send message handlers
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', handleKeyPress);

    // Auto-resize textarea
    messageInput.addEventListener('input', handleTextAreaResize);

    // Update status display when config changes
    [apiUrlInput, modelSelect].forEach(element => {
        element.addEventListener('change', updateStatusDisplay);
    });

    // Debug mode
    debugModeCheckbox.addEventListener('change', handleDebugModeToggle);
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
    apiUrlDisplay.textContent = apiUrlInput.value;
    modelDisplay.textContent = modelSelect.value;
    clearChunkCache();
}

function formatTimestamp(timestamp) {
    return new Intl.DateTimeFormat('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    }).format(timestamp);
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
    const statusText = document.getElementById('status-text');
    const originalContent = statusText.innerHTML;

    if (privacyMode) {
        if (!statusText.innerHTML.includes('🔒 Mode sans trace activé')) {
            statusText.innerHTML = originalContent + ' • <span class="text-orange-600">🔒 Mode sans trace activé</span>';
        }
    } else {
        statusText.innerHTML = originalContent.replace(/ • <span class="text-orange-600">🔒 Mode sans trace activé<\/span>/, '');
    }

    debugLog('Privacy status updated', { privacyMode });
}

function isPrivacyModeEnabled() {
    return localStorage.getItem('privacy-mode') === 'true';
}
// ==========================================
// INITIALIZATION
// ==========================================
function initializeConfig() {
    document.getElementById('initial-timestamp').textContent = formatTimestamp(new Date());
    apiUrlInput.value = DEFAULT_HOST;
    updateStatusDisplay();
    setupEventListeners();

    // Initialize debug mode state
    debugMode = debugModeCheckbox.checked;
    debugLog('Configuration initialized');
}

if (document.readyState === 'loading') {
     document.addEventListener('DOMContentLoaded', initializeConfig);
} else {
    initializeConfig();
}
