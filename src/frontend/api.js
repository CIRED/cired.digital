 // ==========================================
 // ==========================================

 marked.setOptions({
     breaks: true,    // Convert \n to <br>
     gfm: true,       // GitHub Flavored Markdown
     tables: true,    // Table support
     sanitize: false  // We'll use DOMPurify instead
 });

 // fenced tables avec optional language tag (```lang\n|...|\n```)
 const FENCED_TABLE_REGEX = /```(?:\w+)?\s*\n(\|[\s\S]*?\|)\s*\n```/g;

 function renderSafeLLMContent(markdown) {

    const processedMarkdown = markdown.replace(FENCED_TABLE_REGEX, (_, tableContent) => tableContent);

    const rawHtml = marked.parse(processedMarkdown);
    return DOMPurify.sanitize(rawHtml);
}

// ==========================================
// MESSAGE SENDING AND API COMMUNICATION
// ==========================================
async function sendMessage() {
    const query = messageInput.value.trim();
    if (!query || isLoading) return;

    // Hide and remove the input help message
    const inputHelp = document.getElementById('input-help');
    if (inputHelp) {
        inputHelp.classList.add('seen');
        setTimeout(() => {
            inputHelp.style.display = 'none';
            inputHelp.classList.remove('seen');
            }
        , 3000);
    }

    // Momentarily hide the input box
    const inputSection = document.getElementById('input');
    if (inputSection) {
          inputSection.classList.add('seen');
    }

    // Hide all existing messages with a fade-out effect
    Array.from(mainEl.children).forEach(child => {
        child.classList.add('seen');
        setTimeout(() => {
            child.style.display = 'none';
            child.classList.remove('seen');
            if (child.parentNode) {
                child.parentNode.removeChild(child);
            }
        }, 3000);
    });

    // Set loading state
    setLoadingState(true);
    debugLog('Loading state set to true');
    hideError();

    // Add user message and show typing indicator after fade-out and removal
    setTimeout(() => {
        addMessage('user', query);
        resetMessageInput();
        showTyping();
    }, 3000);

    const queryId = 'query_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9);

    debugLog('Starting message send process', { query, queryId, isLoading });


    const config = getConfiguration();
    debugLog('Configuration retrieved', config);

    const requestBody = buildRequestBody(query, config);
    debugLog('Request body built:', requestBody);

    try {
        const startTime = Date.now();
        const response = await makeApiRequest(config.apiUrl, requestBody, queryId);
        debugLog('API request completed', {
            apiUrl: config.apiUrl,
            status: response.status,
            responseTime: `${Date.now() - startTime}ms`,
        });

        const data = await response.json();
        debugLog('Raw server response', data);
        handleResponse(requestBody, data, queryId);

    } catch (err) {
        console.error('Error sending message:', err);
        handleError(err);
    } finally {
        // Clean up
        hideTyping();
        setLoadingState(false);
        inputSection.classList.remove('seen');
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
        maxTokens: parseInt(maxTokensInput.value),
        chunkLimit: parseInt(chunkLimitInput.value, 10),
        searchStrategy: searchStrategySelect.value,
        includeWebSearch: includeWebSearchCheckbox.checked
    };
}

function buildRequestBody(query, config) {
    return {
        query: query,
        search_mode: 'custom',
        search_settings: {
            use_semantic_search: true,
            use_hybrid_search: true,
            search_strategy: config.searchStrategy,
            limit: config.chunkLimit
        },
        rag_generation_config: {
            model: config.model,
            temperature: config.temperature,
            max_tokens: config.maxTokens,
            stream: false
        },
        include_title_if_available: true,
        include_web_search: config.includeWebSearch,
    };
}

async function makeApiRequest(apiUrl, requestBody, queryId) {
    logQuery(
        queryId,
        requestBody.query,
        {
            model: requestBody.rag_generation_config.model,
            temperature: requestBody.rag_generation_config.temperature,
            max_tokens: requestBody.rag_generation_config.max_tokens,
            search_mode: requestBody.search_settings.search_mode
        });

    const response = await fetch(`${apiUrl}/v3/retrieval/rag`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
        const errorData = await response.text();
        debugLog('API request failed', {
            status: response.status,
            statusText: response.statusText,
            errorData,
            url: apiUrl
        });
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response;
}

function handleError(err) {
    debugLog('Error occurred in sendMessage', {
        errorMessage: err.message,
        errorStack: err.stack
    });
    showError(err.message);
    addMessage('bot', `I apologize, but I encountered an error: ${err.message}.`, true);
}

// ==========================================
// RESPONSE HANDLING
// ==========================================
function handleResponse(requestBody, data, queryId) {
    debugLog('Starting response processing', {
        hasContent: !!data.results.generated_answer,
        citationsCount: data.results.citations?.length || 0
    });

    const content = data.results.generated_answer || 'No response generated.';
    const citations = data.results.citations || [];

    const { processedContent, documentBibliography } = processVancouverCitations(content, citations);
    debugLog('Citations processed', {
        originalLength: content.length,
        processedLength: processedContent.length,
        bibliographyCount: Object.keys(documentBibliography).length
    });

    const htmlContent = renderSafeLLMContent(processedContent);

    const botMessage = addMessage('bot', htmlContent);
    addVancouverCitations(botMessage, documentBibliography);
    addFeedbackButtons(botMessage, requestBody, data.results);

    logResponse(queryId, processedContent);
    // Faire réapparaître la searchbox après réponse
    const inputSection = document.getElementById('input-container');
    if (inputSection) {
        inputSection.classList.remove('seen');
    }
}

// ==========================================
// FEEDBACK SYSTEM
// ==========================================
function sendFeedback(requestBody, results, feedback, comment = '') {
    debugLog('Sending feedback', {
        feedback,
        questionLength: requestBody.query.length,
        answerLength: results.generated_answer?.length || 0,
        commentLength: comment.length,
        comment: comment,
        hasComment: comment.length > 0
    });
    const feedbackData = {
        question: requestBody.query,
        answer: results.generated_answer,
        feedback: feedback,
        timestamp: new Date().toISOString(),
        comment: comment || null
    };

    debugLog('Feedback data being sent to server', feedbackData);

    fetch(`${FEEDBACK_HOST}/v1/feedback`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(feedbackData)
    })
    .then(response => {
        if (!response.ok) {
            debugLog('Feedback request failed', { status: response.status });
        } else {
            debugLog('Feedback successfully sent.');
        }
    })
    .catch(error => {
        debugLog('Error sending feedback:', error);
    });
}

// ==========================================
// APPLICATION STARTUP
// ==========================================

function initializeAPI() {
    debugLog('API module initialized');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAPI);
} else {
    initializeAPI();
}
