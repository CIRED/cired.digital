// ==========================================
// MESSAGE CREATION AND DISPLAY
// ==========================================
function createMessage(type, content, timestamp, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message-wrapper ${type === 'user' ? 'user-wrapper' : 'bot-wrapper'}`;
    messageDiv.id = `message-${messageIdCounter++}`;

    const avatarIcon = type === 'user' ? '👤' : '🤖';
    const messageClass = getMessageClass(type, isError);
    const avatarClass = getAvatarClass(type);

    messageDiv.innerHTML = `
        <div class="message-content-wrapper ${type === 'user' ? 'user-content' : 'bot-content'}">
            <div class="avatar ${avatarClass}">
                <span class="avatar-text">${avatarIcon}</span>
            </div>
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

function getMessageClass(type, isError) {
    if (type === 'user') {
        return 'user-message';
    }
    return isError
        ? 'error-message'
        : 'bot-message';
}

function getAvatarClass(type) {
    return type === 'user'
        ? 'user-avatar'
        : 'bot-avatar';
}

function addMessage(type, content, isError = false) {
    debugLog('Adding message to UI', { type, contentLength: content.length, isError });

    const message = createMessage(type, content, new Date(), isError);
    messagesContainer.appendChild(message);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return message;
}

// ==========================================
// TYPING INDICATOR
// ==========================================
function showTyping() {
    debugLog('Showing typing indicator');

    const msg = createMessage(
        'bot',
        `<span class="typing-spinner">⟳</span>Recherche dans la base documentaire…`
    );
    msg.id = 'typing-indicator';
    messagesContainer.appendChild(msg);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
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
    feedbackDiv.className = 'flex gap-2 mt-2 items-center';
    feedbackDiv.innerHTML = `
        <input type="text" class="feedback-input" placeholder="Donnez votre avis sur cette réponse." maxlength="500">
        <button class="feedback-button feedback-up" title="Bonne réponse.">👍</button>
        <button class="feedback-button feedback-down" title="Réponse insuffisante.">👎</button>
    `;

    botMessage.querySelector('.message-content').after(feedbackDiv);

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
