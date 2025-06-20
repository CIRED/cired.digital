const mainEl = document.querySelector('main');

// ==========================================
// MESSAGE CREATION AND DISPLAY
// ==========================================

function createMessage(content, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message-wrapper`;
    messageDiv.id = `message-${messageIdCounter++}`;

    messageDiv.innerHTML = `
        <div class="message-content-wrapper">
            <div class="message-bubble">
                <div class="${messageClass}">
                    <div class="message-content">${content}</div>
                </div>
                <div class="citations-container"></div>
            </div>
        </div>
    `;
    return messageDiv;
}

function addMain(content) {
    debugLog('Adding article to UI', {contentLength: content.length});

    const message = createMessage(content, false);
    messagesContainer.appendChild(message);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return message;
}

function addMainError(content) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = content;
    messagesContainer.appendChild(errorDiv);
}

// ==========================================
// TYPING INDICATOR
// ==========================================
function showTyping() {
    debugLog('Showing typing indicator');

    const msg = createMessage(
        'bot',
        `<span class="typing-spinner">⟳</span>Recherche dans la base documentaire (compter 6-20s)…`
    );
    msg.id = 'typing-indicator';
    mainEl.appendChild(msg);
    mainEl.scrollTop = mainEl.scrollHeight;
    return msg;
}

function hideTyping() {
    debugLog('Hiding typing indicator');
    const typing = document.getElementById('typing-indicator');
    if (typing) {
        typing.remove();
    }
}

// ==========================================
// FEEDBACK BUTTONS
// ==========================================
function addFeedbackButtons(botMessage, requestBody, results) {
    debugLog('Adding feedback buttons to message');

    const feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'feedback-container';
    feedbackDiv.innerHTML = `
        <input type="text" class="feedback-input" placeholder="Donnez votre avis sur cette réponse." maxlength="500">
        <button class="feedback-button feedback-up" title="Bonne réponse.">👍</button>
        <button class="feedback-button feedback-down" title="Réponse insuffisante.">👎</button>
    `;

    // Placer le feedback sous la bibliographie (citations-container)
    const citContainer = botMessage.querySelector('.citations-container');
    if (citContainer) {
        citContainer.after(feedbackDiv);
    } else {
        botMessage.querySelector('.message-content').after(feedbackDiv);
    }

    const commentInput = feedbackDiv.querySelector('input[type="text"]');

    feedbackDiv.querySelector('.feedback-up').addEventListener('click', () => {
        debugLog('User clicked thumbs up');
        sendFeedback(requestBody, results, 'up', commentInput.value.trim());
        feedbackDiv.remove();
    });

    feedbackDiv.querySelector('.feedback-down').addEventListener('click', () => {
        debugLog('User clicked thumbs down');
        sendFeedback(requestBody, results, 'down', commentInput.value.trim());
        feedbackDiv.remove();
    });
}
