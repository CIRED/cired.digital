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

        insertArticle(requestBody, data, queryId);
    } catch (err) {
        handleError(err);
    } finally {
        animateWaitEnd();
        debugLog('Message processing completed');
    }
}

async function animateWaitStart(query) {
    // Fade out
    setLoadingState(true);

    inputHelp.classList.add('seen');
    Array.from(messagesContainer.children).forEach(child => child.classList.add('seen'));
  //  Array.from(mainEl.children).forEach(child => child.classList.add('seen'));

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
    addMainError(`I apologize, but I encountered an error: ${err.message}.`, true);
}

// ==========================================
// RESPONSE HANDLING
// ==========================================

function insertArticle(requestBody, data, queryId) {
    debugLog('Starting response processing', {
        hasContent: !!data.results.generated_answer,
        citationsCount: data.results.citations?.length || 0
    });

    const citations = data.results.citations || [];
    const { citationToDoc, bibliography } = processCitations(citations);

    const content = data.results.generated_answer || 'No response generated.';
    replyText = renderFromLLM(content);

    const htmlContent =
        replyTitle(requestBody) +
        replaceCitationMarkers(replyText, citationToDoc) +
        createBibliographyHtml(bibliography);

    const article = addMain(htmlContent);

    // lier les tooltips de citation
    article.querySelectorAll('.citation-bracket').forEach(el => {
      el.addEventListener('mouseover', ev => showChunkTooltip(ev, el));
      el.addEventListener('mouseout',  () => hideChunkTooltip());
    });

    addFeedbackButtons(article, requestBody, data.results);

    logResponse(queryId, replyText);
}

function replyTitle(requestBody) {
    const today = new Date();
    const dayDate = today.toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

    return `<h2>${escapeHtml(requestBody.query)}</h2>
            <div><em>Generated by Cirdi on ${dayDate}</em></div>
            <hr/>
    `;
}

// Helper to escape HTML in the query
function escapeHtml(text) {
    return text.replace(/[&<>"']/g, function (m) {
        return ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        })[m];
    });
}

// Helper to safely render Markdown in model's reply.
// Use the marked and purify libraries

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
