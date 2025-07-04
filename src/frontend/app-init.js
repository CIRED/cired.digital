// ==========================================
// ==========================================

let isLoading = false;
let articleIdCounter = 1;
let sessionId = null;
let sessionStartTime = null;
let statusInterval = null;
let feedbackInterval = null;
let currentArticleIndex = -1;

// ==========================================
// DOM ELEMENTS
// ==========================================
const messagesContainer = document.getElementById('messages-container');
const userInput = document.getElementById('user-input');

// ==========================================
// EVENT LISTENERS SETUP
// ==========================================

function setupPageEventListeners() {

    attach('user-input', 'keydown', handleUserInputKeyDown);
    attach('send-btn', 'click', processInput);

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

function handleUserInputKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        processInput();
    }
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
     * It is safe for filenames and URL: only alphanums and _.
     * (but server side should sanitize too, internet transmission may be insecure)
     */
    const randomBytes = new Uint8Array(9);
    window.crypto.getRandomValues(randomBytes);
    const randomString = Array.from(randomBytes).map(b => b.toString(36)).join('');
    return 'session_' + Date.now() + '_' + randomString.replace(/[^a-zA-Z0-9_]/g, '');
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

async function initializeApp() {
  try {
    setupPageEventListeners();

    initializeSettings();
    initializeHelp();
    initializeProfile();
    initializeOnBoarding();

    debugLog('App initialized');
  } catch (err) {
    addMainError("Initialization failed: " + err.message);
    console.error('Initialization error:', err);
  }
}

if (document.readyState === 'loading') {
     document.addEventListener('DOMContentLoaded', () => {
         initializeApp();
     });
} else {
    initializeApp();
}
