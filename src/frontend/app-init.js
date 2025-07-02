// ==========================================
// ==========================================
const DEFAULT_HOST = 'http://localhost:7272';


let isLoading = false;
let articleIdCounter = 1;
let sessionId = null;
let sessionStartTime = null;
let statusInterval = null;
let feedbackInterval = null;
let currentArticleIndex = -1;
const MAX_INPUT_HEIGHT = 120;

// ==========================================
// DOM ELEMENTS
// ==========================================
const mainDiv = document.querySelector('main');
const messagesContainer = document.getElementById('messages-container');
const inputDiv = document.getElementById('input');
const userInput = document.getElementById('user-input');
const inputHelp = document.getElementById('input-help');

// ==========================================
// EVENT LISTENERS SETUP
// ==========================================

function setupPageEventListeners() {

    userInput.addEventListener('input', function() {
        // Auto-resize the input field
        this.style.height = 'auto';
        // But no more than 120px tall
        this.style.height = Math.min(this.scrollHeight, MAX_INPUT_HEIGHT) + 'px';
    });

    const sendBtn = document.getElementById('send-btn');
    if (sendBtn) {
        sendBtn.addEventListener('click', processInput);
    }

    userInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        // Don't add a new line
        e.preventDefault();
        // Process the message
        sendBtn.click();
    }
    });

    initializeSession();

    document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") {
        logSessionEnd();
    }
    });

    // Replace with modal dialog
    document.getElementById('view-analytics-link').addEventListener('click', function(e) {
        e.preventDefault();
        window.open(cirdiURLInput.value.replace(/\/$/, '') + '/v1/view/privacy', '_blank');
    });

}


function logSessionEnd() {
    if (sessionStartTime) {
        monitor(MonitorEventType.SESSION_END, {
            sessionId: sessionId,
            endTime: new Date().toISOString(),
            sessionDuration: Date.now() - sessionStartTime,
            endReason: 'visibility_change',
            userAgent: navigator.userAgent
        });
    }
};



// ==========================================
// SESSION MANAGEMENT
// ==========================================
function generateSessionId() {
    /*
     * Generate a unique session ID based on the current timestamp and a random string.
     *
     * This ID is used to track user sessions and interactions.
     * It is 100% safe for filenames and URL: only alphanums and _.
     */
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
            .replace(/[^a-zA-Z0-9_]/g, '');
}

function initializeSession() {
    sessionId = localStorage.getItem('session-id');
    if (!sessionId) {
        sessionId = generateSessionId();
        localStorage.setItem('session-id', sessionId);
    }

    // Gather technical context
    profileOrNothing = getProfile() || null;
    const technicalContext = {
        sessionId: sessionId,
        userAgent: navigator.userAgent,
        language: navigator.language || navigator.userLanguage,
        screen: {
            width: window.screen.width,
            height: window.screen.height,
            pixelRatio: window.devicePixelRatio
        },
        profile: profileOrNothing
    };
    monitor(MonitorEventType.SESSION, technicalContext);
    sessionStartTime = Date.now();
}

// ==========================================
// INITIALIZATION
// ==========================================

async function initializeConfig() {
  if (!loadEnvironmentSettings()) {
    addMainError("Settings initialization failed. Check console for details.");
    return;
  }
  try {
    if (!settings) throw new Error("Settings not loaded. Make sure settings.js is included before settings.js.");
    populateFormFromSettings(settings);

    setupPageEventListeners();
    setupSettingsListeners();

    initializeProfile();

    debugLog('Configuration initialized');
  } catch (err) {
    addMainError("Initialization failed: " + err.message);
    console.error('Initialization error:', err);
  }
}

if (document.readyState === 'loading') {
     document.addEventListener('DOMContentLoaded', () => {
         initializeConfig();
     });
} else {
    initializeConfig();
}
