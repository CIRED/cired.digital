// ==========================================
// MAIN CONTENTS CREATION AND DISPLAY
// ==========================================

function addMain(content) {
    debugLog('Adding article to main content zone', { contentLength: content.length });
    const articleEl = document.createElement('article');
    articleEl.id = `article-${articleIdCounter++}`;
    articleEl.innerHTML = content;
    messagesContainer.appendChild(articleEl);
    return articleEl;
}

function addMainError(content) {
    debugLog('Adding error message to main content zone', { contentLength: content.length });
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = content;
    messagesContainer.prepend(errorDiv);
}

function showTyping() {
    debugLog('Showing typing indicator');
    hideTyping();
    const spinnerDiv = document.createElement('div');
    spinnerDiv.id = 'typing-indicator';
    spinnerDiv.innerHTML = '<span class="typing-spinner">⟳</span>Recherche dans la base documentaire (compter 6-20s)…';
    mainEl.appendChild(spinnerDiv);
}

function hideTyping() {
    debugLog('Hiding typing indicator');
    document.getElementById('typing-indicator')?.remove();
}

// ==========================================
// FEEDBACK
// ==========================================

function addFeedbackButtons(article, requestBody, results) {
    debugLog('Adding feedback buttons to message');

    const feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'feedback-container';
    feedbackDiv.innerHTML = `
        <input type="text" class="feedback-input" placeholder="Donnez votre avis sur cette réponse." maxlength="500">
        <button class="feedback-button feedback-up" title="Bonne réponse.">👍</button>
        <button class="feedback-button feedback-down" title="Réponse insuffisante.">👎</button>
    `;

    // Placer le feedback après le contenu de l'article
    article.appendChild(feedbackDiv);

    const commentInput = feedbackDiv.querySelector('input[type="text"]');

    feedbackDiv.querySelector('.feedback-up').addEventListener('click', () => {
        debugLog('User clicked thumbs up');
        sendFeedback('up', commentInput.value.trim(), results);
        feedbackDiv.remove();
    });

    feedbackDiv.querySelector('.feedback-down').addEventListener('click', () => {
        debugLog('User clicked thumbs down');
        sendFeedback('down', commentInput.value.trim(), results);
        feedbackDiv.remove();
    });
}

function sendFeedback(feedback, comment = '', results = {}) {
    debugLog('Sending feedback', {
        feedback,
        commentLength: comment.length,
        comment: comment,
        hasComment: comment.length > 0
    });
    const feedbackData = {
        session_id: typeof sessionId !== 'undefined' ? sessionId : '',
        query_id: results.query_id || '',
        feedback: feedback,
        comment: comment || null
    };

    debugLog('Feedback data being sent to server', feedbackData);

    fetch(analyticsEndpoint(feedback), {
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
