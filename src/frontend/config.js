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

// Status display elements
const apiUrlDisplay = document.getElementById('api-url-display');
const modelDisplay = document.getElementById('model-display');

// ==========================================
// INITIALIZATION
// ==========================================
function initialize() {
    document.getElementById('initial-timestamp').textContent = formatTimestamp(new Date());
    apiUrlInput.value = DEFAULT_HOST;
    updateStatusDisplay();
    setupEventListeners();
}

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
