// ==========================================
// MESSAGE CREATION AND DISPLAY
// ==========================================
function createMessage(type, content, timestamp, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `flex ${type === 'user' ? 'justify-end' : 'justify-start'}`;
    messageDiv.id = `message-${messageIdCounter++}`;

    const avatarIcon = type === 'user' ? '👤' : '🤖';
    const messageClass = getMessageClass(type, isError);

    messageDiv.innerHTML = `
        <div class="flex max-w-3xl ${type === 'user' ? 'flex-row-reverse' : 'flex-row'}">
            <div class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${getAvatarClass(type)}">
                <span class="font-bold text-lg">${avatarIcon}</span>
            </div>
            <div class="flex-1">
                <div class="${messageClass} px-4 py-3 rounded-lg">
                    <div class="message-content">${content}</div>
                </div>
                <div class="citations-container"></div>
                <div class="text-xs text-gray-500 mt-1">${formatTimestamp(timestamp)}</div>
            </div>
        </div>
    `;

    return messageDiv;
}

function getMessageClass(type, isError) {
    if (type === 'user') {
        return 'bg-blue-600 text-white';
    }
    return isError
        ? 'bg-red-50 text-red-800 border border-red-200'
        : 'bg-white text-gray-800 border border-gray-200';
}

function getAvatarClass(type) {
    return type === 'user'
        ? 'bg-blue-600 text-white ml-3'
        : 'bg-gray-200 text-gray-600 mr-3';
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
        `<span class="mr-2 inline-block animate-spin text-blue-500">⟳</span>Recherche dans la base documentaire…`
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
    feedbackDiv.className = 'flex gap-2 mt-2';
    feedbackDiv.innerHTML = `
        <button class="thumb-up text-green-600 hover:text-green-800" title="Bonne réponse.">👍</button>
        <button class="thumb-down text-red-600 hover:text-red-800" title="Réponse insuffisante.">👎</button>
    `;

    botMessage.querySelector('.message-content').after(feedbackDiv);

    // Add event listeners for feedback buttons
    feedbackDiv.querySelector('.thumb-up').addEventListener('click', () => {
        debugLog('User clicked thumbs up');
        sendFeedback(requestBody, results, 'up');
        feedbackDiv.remove();
    });

    feedbackDiv.querySelector('.thumb-down').addEventListener('click', () => {
        debugLog('User clicked thumbs down');
        sendFeedback(requestBody, results, 'down');
        feedbackDiv.remove();
    });
}
