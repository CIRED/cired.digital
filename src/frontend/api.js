// ==========================================
// MESSAGE SENDING AND API COMMUNICATION
// ==========================================
async function sendMessage() {
    const query = messageInput.value.trim();
    if (!query || isLoading) return;

    // Set loading state
    setLoadingState(true);
    hideError();

    // Add user message and show typing indicator
    addMessage('user', query);
    resetMessageInput();
    const typingMSG = showTyping();

    try {
        const config = getConfiguration();
        const requestBody = buildRequestBody(query, config);

        console.log('Sending request:', requestBody);

        const response = await makeApiRequest(config.apiUrl, requestBody);
        const data = await response.json();

        handleResponse(requestBody, data);

    } catch (err) {
        console.error('Error sending message:', err);
        handleError(err);
    } finally {
        // Clean up
        hideTyping();
        setLoadingState(false);
        messageInput.focus();
    }
}

function setLoadingState(loading) {
    isLoading = loading;
    sendBtn.disabled = loading;
}

function resetMessageInput() {
    messageInput.value = '';
    messageInput.style.height = 'auto';
}

function getConfiguration() {
    return {
        apiUrl: apiUrlInput.value,
        model: modelSelect.value,
        temperature: parseFloat(temperatureInput.value),
        maxTokens: parseInt(maxTokensInput.value)
    };
}

function buildRequestBody(query, config) {
    return {
        query: query,
        search_settings: {
            search_mode: 'advanced',
            limit: 10
        },
        rag_generation_config: {
            model: config.model,
            temperature: config.temperature,
            max_tokens: config.maxTokens,
            stream: false
        }
    };
}

async function makeApiRequest(apiUrl, requestBody) {
    const response = await fetch(`${apiUrl}/v3/retrieval/rag`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
        const errorData = await response.text();
        console.error('API Error Response:', errorData);
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response;
}

function handleError(err) {
    showError(err.message);
    addMessage('bot', `I apologize, but I encountered an error: ${err.message}. Please check your R2R configuration and try again.`, true);
}

// ==========================================
// RESPONSE HANDLING
// ==========================================
function handleResponse(requestBody, data) {
    console.log('Processing response:', data);

    const content = data.results.generated_answer || 'No response generated.';
    const citations = data.results.citations || [];

    const { processedContent, documentBibliography } = processVancouverCitations(content, citations);

    const botMessage = addMessage('bot', processedContent);
    addVancouverCitations(botMessage, documentBibliography);
    addFeedbackButtons(botMessage, requestBody, data.results);
}

// ==========================================
// FEEDBACK SYSTEM
// ==========================================
function sendFeedback(requestBody, results, feedback) {
    const feedbackData = {
        question: requestBody.query,
        answer: results.generated_answer,
        feedback: feedback,
        timestamp: new Date().toISOString()
    };

    fetch(`${FEEDBACK_HOST}/v1/feedback`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(feedbackData)
    })
    .then(response => {
        if (!response.ok) {
            console.error('Feedback not accepted by server:', response.status);
        } else {
            console.log('Feedback successfully sent.');
        }
    })
    .catch(error => {
        console.error('Error sending feedback:', error);
    });
}

// ==========================================
// APPLICATION STARTUP
// ==========================================

function initialize() {
    // Initialize privacy mode
    initializePrivacyMode();
    
    document.getElementById('view-analytics-link').addEventListener('click', function(e) {
        e.preventDefault();
        window.open(FEEDBACK_HOST + '/v1/feedback/view', '_blank');
    });
    
    document.getElementById('privacy-policy-link').addEventListener('click', function(e) {
        e.preventDefault();
        alert('Privacy policy coming soon!');
    });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
} else {
    initialize();
}
