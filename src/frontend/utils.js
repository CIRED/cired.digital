// utils.js
// Utility functions for the frontend application

// Render Markdown in model's reply using marked, then sanitizes using DOMPurify

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
// Observability: Log to the analytics server
// ===========================================

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

async function logRequest(queryId, query, config, requestBody) {
    try {
        const privacyMode = isPrivacyModeEnabled();
        const requestData = {
            session_id: sessionId,
            query_id: queryId,
            query: query,
            config: config,
            request_body: requestBody,
            timestamp: new Date().toISOString(),
            privacy_mode: privacyMode
        };
        const response = await fetch(`${FEEDBACK_HOST}/v1/log/request`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        if (response.ok) {
            debugLog('Request logged successfully');
        } else {
            console.warn('Request logging failed:', response.status);
        }
    } catch (error) {
        console.error('Error logging request:', error);
    }
}

async function logResponse(queryId, response, processingTime) {
    try {
        const privacyMode = isPrivacyModeEnabled();

        const responseData = {
            session_id: sessionId,
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

        debugLog('Response logging status', { status: responseResult.status, ok: responseResult.ok , responseResult});
    } catch (error) {
        console.error('Error logging response:', error);
    }
}

async function logArticle(sessionId, queryId, article) {
    try {
        const privacyMode = isPrivacyModeEnabled();
        const articleData = {
            session_id: sessionId,
            query_id: queryId,
            article: article,
            timestamp: new Date().toISOString(),
            privacy_mode: privacyMode
        };
        const response = await fetch(`${FEEDBACK_HOST}/v1/log/article`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(articleData)
        });
        debugLog('Article logging response', { status: response.status, ok: response.ok , response});
    } catch (error) {
        console.error('Error logging article:', error);
    }
}
