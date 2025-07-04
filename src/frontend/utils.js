// utils.js
// Utility functions for the frontend application

function attach(id, event, handler) {
  // Defensively attach an event listener to an element by ID
  // If the element is not found, log a warning
  if (!id || !handler) {
    console.warn(`attach called with invalid parameters: id=${id}, handler=${handler}`);
    return;
  }
  const element = document.getElementById(id);
  if (element) {
    element.addEventListener(event, handler);
  } else {
    console.warn(`Element not found for ID: ${id}`);
  }
}

// ===========================================
// Render Markdown in model's reply using marked, then sanitizes using DOMPurify
// ===========================================

marked.setOptions({
     breaks: true,    // Convert \n to <br>
     gfm: true,       // GitHub Flavored Markdown
     tables: true,    // Table support
     sanitize: false  // We'll use DOMPurify instead
 });

 function renderFromLLM(markdown) {
    // Sometimes the LLM fence tables in ```table or ```md blocks. Remove those fences.
    const FENCED_TABLE_REGEX = /```(?:\w+)?\s*\n(\|[\s\S]*?\|)\s*\n```/g;
    const processedMarkdown = markdown.replace(FENCED_TABLE_REGEX, (_, tableContent) => tableContent);

    const rawHtml = marked.parse(processedMarkdown);
    return DOMPurify.sanitize(rawHtml);
}

// Escape HTML special characters in a string
function escapeHtml(text) {
    if (!text) return '';
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Debug logging, only active if debug mode is enabled.
function debugLog(message, data = null) {
    if (!debugModeOn()) return;
    if (data !== null) {
        console.log("[DEBUG]", message, data);
    } else {
        console.log("[DEBUG]", message);
    }
}

// ===========================================
// Observability: Monitor to the analytics server
// ===========================================

const MonitorEventType = {
    SESSION_START: "sessionStart",
    USER_INPUT: "userInput",
    REQUEST: "request",
    RESPONSE: "response",
    ARTICLE: "article",
    FEEDBACK: "feedback",
    USER_PROFILE: "userProfile",
    VISIBILITY_CHANGE: "visibilityChange",
};

// Note: Using fetch for all events - sendBeacon had CORS issues
async function monitor(eventType, payload) {
    const telemetryCheckbox = document.getElementById('telemetry-mode');
    if (!telemetryCheckbox || !telemetryCheckbox.checked) return;

    if (!Object.values(MonitorEventType).includes(eventType)) {
        debugLog('Invalid monitor event type', eventType);
        return;
    }
    const cirdiURLInput = document.getElementById('cirdi-url');
    if (!cirdiURLInput || !cirdiURLInput.value) {
        console.warn('CIRDI URL input not found or empty');
        return;
    }
    const analyticsEndpoint = cirdiURLInput.value.replace(/\/$/, '') + '/v1/monitor'
    const timestamp = new Date().toISOString().replace(/[^a-zA-Z0-9]/g, '');
    const data = {
        sessionId,
        timestamp,
        eventType,
        payload
    };

    try {
        // Use fetch for all events
        const response = await fetch(analyticsEndpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
            keepalive: true,  // Keep alive during page unload
            credentials: 'omit'  // Don't send credentials to avoid CORS issues
        });
        debugLog('[MONITOR] event sent via fetch', { eventType, status: response.status, ok: response.ok });
    } catch (error) {
        console.error('Error sending monitor event:', error);
    }
}

// Generates a random UUID v4
function generateUUID() {
    return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
}
