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


function logFeedback(type, comment) {
    debugLog('Logging feedback', { type, comment });
    monitor(MonitorEventType.FEEDBACK, {
        type,
        comment: comment || ''
    });
}

function addFeedback(article) {
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
        logFeedback('up', commentInput.value.trim());
        feedbackDiv.remove();
        
        if (typeof onFeedbackCompleted === 'function' && !isOnboarded()) {
            onFeedbackCompleted();
        }
    });

    feedbackDiv.querySelector('.feedback-down').addEventListener('click', () => {
        logFeedback('down', commentInput.value.trim());
        feedbackDiv.remove();
        
        if (typeof onFeedbackCompleted === 'function' && !isOnboarded()) {
            onFeedbackCompleted();
        }
    });
}
