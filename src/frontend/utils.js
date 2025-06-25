// utils.js
// Utility functions for the frontend application


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

// Debug logging, conditional on a global debugMode variable
function debugLog(message, data = null) {
    if (typeof debugMode !== "undefined" && debugMode) {
        if (data !== null) {
            console.log("[DEBUG]", message, data);
        } else {
            console.log("[DEBUG]", message);
        }
    }
}

// ===========================================
// Observability: Monitor to the analytics server
// ===========================================

const MonitorEventType = {
    SESSION: "session",
    REQUEST: "request",
    RESPONSE: "response",
    ARTICLE: "article",
    FEEDBACK: "feedback",
    USER_PROFILE: "userProfile",
    SESSION_END: "sessionEnd"
};

async function monitor(eventType, payload) {
    if (isPrivacyModeEnabled()) return;
    if (!Object.values(MonitorEventType).includes(eventType)) {
        debugLog('Invalid monitor event type', eventType);
        return;
    }
    const analyticsEndpoint = feedbackUrlInput.value.replace(/\/$/, '') + '/v1/monitor'
    const timestamp = new Date().toISOString().replace(/[^a-zA-Z0-9]/g, '');
    const data = {
        sessionId,
        timestamp,
        eventType,
        payload
    };
    try {
        const response = await fetch(analyticsEndpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        debugLog('Monitor event sent', { eventType, status: response.status, ok: response.ok });
    } catch (error) {
        console.error('Error sending monitor event:', error);
    }
}
