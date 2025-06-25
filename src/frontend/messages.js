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
        <button class="clipboard-button" title="Copier l'article dans le presse-papiers">📋</button>
        <button class="feedback-button feedback-up" title="Bonne réponse.">👍</button>
        <button class="feedback-button feedback-down" title="Réponse insuffisante.">👎</button>
    `;

    // Placer le feedback après le contenu de l'article
    article.appendChild(feedbackDiv);

    const commentInput = feedbackDiv.querySelector('input[type="text"]');
    const clipboardBtn = feedbackDiv.querySelector('.clipboard-button');

    clipboardBtn.addEventListener('click', () => {
        copyArticleToClipboard(article);
    });

    feedbackDiv.querySelector('.feedback-up').addEventListener('click', () => {
        logFeedback('up', commentInput.value.trim());
        showFeedbackSuccess(feedbackDiv);

        if (typeof onFeedbackCompleted === 'function' && !isOnboarded()) {
            onFeedbackCompleted();
        }
    });

    feedbackDiv.querySelector('.feedback-down').addEventListener('click', () => {
        logFeedback('down', commentInput.value.trim());
        showFeedbackSuccess(feedbackDiv);

        if (typeof onFeedbackCompleted === 'function' && !isOnboarded()) {
            onFeedbackCompleted();
        }
    });
}
function showFeedbackSuccess(feedbackDiv) {
    feedbackDiv.innerHTML = '<div class="feedback-success">Merci pour votre retour</div>';
}

function copyArticleToClipboard(article) {
    const articleClone = article.cloneNode(true);
    const feedbackContainer = articleClone.querySelector('.feedback-container');
    
    if (feedbackContainer) feedbackContainer.remove();
    
    const htmlContent = articleClone.innerHTML;
    
    navigator.clipboard.writeText(htmlContent).then(() => {
        debugLog('Article copied to clipboard');
        const clipboardBtn = article.querySelector('.clipboard-button');
        const originalText = clipboardBtn.textContent;
        clipboardBtn.textContent = '✓';
        setTimeout(() => {
            clipboardBtn.textContent = originalText;
        }, 1000);
    }).catch(err => {
        console.error('Failed to copy to clipboard:', err);
        fallbackCopyToClipboard(htmlContent);
    });
}

function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    try {
        document.execCommand('copy');
        debugLog('Article copied to clipboard (fallback)');
    } catch (err) {
        console.error('Fallback copy failed:', err);
    }
    document.body.removeChild(textArea);
}
