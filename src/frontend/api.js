// ==========================================
// INPUT PROCESSING AND API COMMUNICATION
// ==========================================

async function processInput() {
    const query = userInput.value.trim();
    if (!query || isLoading) return;

    animateWaitStart(query);

    const queryId = 'query_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9);
    debugLog('Starting message send process', { query, queryId, isLoading });

    const config = getConfiguration();
    debugLog('Configuration retrieved', config);

    const requestBody = buildRequestBody(query, config);
    debugLog('Request body built:', requestBody);

    monitor(MonitorEventType.REQUEST, {
        queryId,
        query,
        config,
        requestBody
    });

    try {
        const startTime = Date.now();
        const response = await makeApiRequest(config.apiUrl, requestBody, queryId);
        const duration = Date.now() - startTime
        debugLog('API request completed', {
            apiUrl: config.apiUrl,
            status: response.status,
            responseTime: `${duration}ms`,
        });

        const data = await response.json();
        debugLog('Raw server response', data);

        monitor(MonitorEventType.RESPONSE, {
            queryId,
            response: data,
            processingTime: duration,
            timestamp: new Date().toISOString()
        });

        insertArticle(config, requestBody, data, queryId, duration);
    } catch (err) {
        handleError(err);
    } finally {
        animateWaitEnd();
        debugLog('Message processing completed');
    }
}

async function animateWaitStart() {
    // Fade out
    setLoadingState(true);

    inputHelp.classList.add('seen');
    Array.from(messagesContainer.children).forEach(child => child.classList.add('seen'));

    // Await fade-out (3s as defined in CSS for .seen class)
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Remove from display flow
    inputHelp.style.display = 'none';
    Array.from(messagesContainer.children).forEach(child => {
        child.style.display = 'none';
    });

    // Show user message and spinner
    if (isLoading) {
        showTyping();
    }
}

function animateWaitEnd() {
        hideTyping();
        setLoadingState(false);
        inputDiv.classList.remove('seen');
        userInput.focus();
}

function setLoadingState(loading) {
    isLoading = loading;
    sendBtn.disabled = loading;
    debugLog('Loading state set to ' + loading);
}

function resetMessageInput() {
    userInput.value = '';
    userInput.style.height = 'auto';
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
    addMainError(`I apologize, but I encountered an error: ${err.message}.`, true);
}

// ==========================================
// RESPONSE HANDLING
// ==========================================

function insertArticle(config, requestBody, data, queryId, duration) {
    debugLog('Starting response processing', {
        hasContent: !!data.results.generated_answer,
        citationsCount: data.results.citations?.length || 0
    });

    const citations = data.results.citations || [];
    const { citationToDoc, bibliography } = processCitations(citations);

    const content = data.results.generated_answer || 'No response generated.';
    replyText = renderFromLLM(content);

    const htmlContent =
        replyTitle(config, requestBody, data, duration) +
        replaceCitationMarkers(replyText, citationToDoc) +
        createBibliographyHtml(bibliography);

    monitor(MonitorEventType.ARTICLE, {
        queryId,
        htmlContent,
    });

    const article = addMain(htmlContent);

    // lier les tooltips de citation
    article.querySelectorAll('.citation-bracket').forEach(el => {
      el.addEventListener('mouseover', ev => showChunkTooltip(ev, el));
      el.addEventListener('mouseout',  () => hideChunkTooltip());
    });

    addFeedback(article);
    
    if (typeof onFirstResponseCompleted === 'function' && !isOnboarded()) {
        onFirstResponseCompleted();
    }

    // Update stats visibility after article is inserted
    updateStatsVisibility();
}

// Dynamically show/hide stats divs based on debugMode
function updateStatsVisibility() {
    const showStats = typeof debugMode !== "undefined" && debugMode;
    document.querySelectorAll('.generation-stats, .config-stats').forEach(el => {
        el.style.display = showStats ? '' : 'none';
    });
}

function replyTitle(config, requestBody, data, duration) {
    const today = new Date();
    const dayDate = today.toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

    const costs = estimateCosts(config, data.results, duration);
    const costEl = presentEconomics(costs);

    // Always render the divs, but let updateStatsVisibility control their display
    return `<h2>${escapeHtml(requestBody.query)}</h2>
            <div class="attribution">Generated by Cirdi on ${dayDate}</div>
            <div class="generation-stats">${costEl}</div>
            <div class="config-stats">Retrieval en mode ${config.searchStrategy} limité à ${config.chunkLimit} segments. Génération avec ${config.model} limité à ${config.maxTokens} tokens out.</div>
            <hr/>
    `;
}
