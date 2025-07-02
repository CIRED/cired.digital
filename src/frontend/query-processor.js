// ==========================================
// QUERY PROCESSING AND API COMMUNICATION
// ==========================================

async function processInput() {
    if (!validateInput()) return;

    const context = prepareQueryContext();
    try {
        uiProcessingStart();
        const response = await executeQuery(context);
        uiProcessingRetrievalDone(response.duration);
        finalResult = await processStream(response);
        uiProcessingGenerationDone(finalResult.duration);
        monitor(MonitorEventType.RESPONSE, {
            queryId: context.queryId,
            response: finalResult,
            retrievalTime: response.duration,
            generationTime: finalResult.duration,
            timestamp: new Date().toISOString()
        });
        insertArticle(context.settings, context.requestBody, finalResult, context.queryId, response.duration);
    } finally {
        uiProcessingEnd();
        debugLog('Message processing completed');
    }
}

function validateInput() {
    const query = userInput.value.trim();
    return query && !isLoading;
}

function prepareQueryContext() {
    const query = userInput.value.trim();
    const queryId = 'query_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9);
    const settings = getSettings();
    const requestBody = buildRequestBody(query, settings);

    debugLog('Starting message send process', { query, queryId, isLoading });
    debugLog('Configuration retrieved', settings);
    debugLog('Request body built:', requestBody);

    return { query, queryId, settings, requestBody };
}

async function executeQuery(context) {
    monitor(MonitorEventType.REQUEST, {
        queryId: context.queryId,
        query: context.query,
        settings: context.settings,
        requestBody: context.requestBody
    });

    try {
        const startTime = Date.now();
        const response = await makeApiRequest(context.settings.r2rURL, context.requestBody);
        const duration = Date.now() - startTime;

        debugLog('API request completed', {
            r2rURL: context.settings.r2rURL,
            status: response.status,
            responseTime: `${duration}ms`,
        });

        return { response, duration };
    } catch (err) {
        handleError(err);
        throw err;
    }
}

function resetMessageInput() {
    userInput.value = '';
    userInput.style.height = 'auto';
}

function buildRequestBody(query, settings) {
    return {
        query: query,
        search_mode: 'custom',
        search_settings: {
            use_semantic_search: true,
            use_hybrid_search: true,
            search_strategy: settings.searchStrategy,
            limit: settings.chunkLimit
        },
        rag_generation_settings: {
            model: settings.model,
            temperature: settings.temperature,
            max_tokens: settings.maxTokens,
            stream: true
        },
        include_title_if_available: true,
        include_web_search: settings.includeWebSearch,
    };
}

async function makeApiRequest(r2rURL, requestBody) {
    const response = await fetch(`${r2rURL}/v3/retrieval/rag`, {
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
            url: r2rURL
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

function insertArticle(settings, requestBody, data, queryId, duration) {
    debugLog('Starting response processing', {
        hasContent: !!data.results.generated_answer,
        citationsCount: data.results.citations?.length || 0
    });

    const citations = data.results.citations || [];
    const { citationToDoc, bibliography } = processCitations(citations);

    const content = data.results.generated_answer || 'No response generated.';
    replyText = renderFromLLM(content);

    const htmlContent =
        replyTitle(settings, requestBody, data, duration) +
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
    addCarouselControls();
    updateCarouselControls();

    if (typeof onFirstResponseCompleted === 'function' && !isOnboarded()) {
        onFirstResponseCompleted();
    }

    // Update stats visibility after article is inserted
    updateStatsVisibility();
}

// Dynamically show/hide stats divs based on debugMode
function updateStatsVisibility() {
    const showStats = debugModeOn();
    document.querySelectorAll('.generation-stats, .settings-stats').forEach(el => {
        el.style.display = showStats ? '' : 'none';
    });
}

function replyTitle(settings, requestBody, data, duration) {
    const today = new Date();
    const dayDate = today.toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

    const costs = estimateCosts(settings, data.results, duration);
    const costEl = presentEconomics(costs);

    // Always render the divs, but let updateStatsVisibility control their display
    return `<h2>${escapeHtml(requestBody.query)}</h2>
            <div class="attribution">Generated by Cirdi on ${dayDate}</div>
            <div class="generation-stats">${costEl}</div>
            <div class="settings-stats">Retrieval en mode ${settings.searchStrategy} limité à ${settings.chunkLimit} segments. Génération avec ${settings.model} limité à ${settings.maxTokens} tokens out.</div>
            <hr/>
    `;
}

attach('debug-mode', 'change', updateStatsVisibility);
