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
    const message = createMessage(type, content, new Date(), isError);
    messagesContainer.appendChild(message);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return message;
}

// ==========================================
// CITATION PROCESSING WITH MESSAGE CONTEXT
// ==========================================
function processMessageWithCitations(content, citations, messageElement) {
    // Extract message ID for unique citation linking
    const messageId = messageElement.id;

    // Process citations with message context
    const result = processVancouverCitations(content, citations, messageId);

    // Update message content with processed citations
    const contentElement = messageElement.querySelector('.message-content');
    contentElement.innerHTML = result.processedContent;

    // Add bibliography to message
    addVancouverCitations(messageElement, result.documentBibliography);

    return result;
}

// ==========================================
// TYPING INDICATOR
// ==========================================
function showTyping() {
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
    const typing = document.getElementById('typing-indicator');
    if (typing) {
        typing.remove();
    }
}

// ==========================================
// VANCOUVER CITATIONS PROCESSING (SIMPLIFIED)
// ==========================================
function processVancouverCitations(content, citations, messageId = null) {
    const documentMap = new Map();
    const citationToDoc = new Map();
    let docNumber = 1;

    // Generate unique message identifier for this set of citations
    const questionNumber = messageId || `msg-${Date.now()}`;

    // Process each citation
    citations.forEach(citation => {
        const payload = citation.payload || citation;
        const metadata = payload.metadata || {};

        const documentInfo = extractDocumentInfo(metadata, payload);
        const docKey = documentInfo.doi || documentInfo.halid || documentInfo.title;

        // Create or get document entry
        if (!documentMap.has(docKey)) {
            documentMap.set(docKey, {
                docNumber: docNumber++,
                documentId: generateDocumentId(documentInfo, questionNumber), // Pass question number
                questionNumber: questionNumber, // Store question number
                ...documentInfo,
                citations: [],
                chunkCounter: 0 // Track chunks within this document
            });
        }

        const doc = documentMap.get(docKey);
        const citationId = citation.id || payload.id || '';
        const fullChunkId = payload.id || citation.id || '';

        // Increment chunk counter and generate letter suffix
        doc.chunkCounter++;
        const letterSuffix = String.fromCharCode(96 + doc.chunkCounter); // 97='a', 98='b', etc.

        // Add citation to document
        doc.citations.push({
            id: citationId,
            text: payload.text || citation.text || '',
            score: payload.score || citation.score || 0,
            letterSuffix: letterSuffix
        });

        // Map citation ID to document info with letter suffix
        citationToDoc.set(citationId, {
            docNumber: doc.docNumber,
            documentId: doc.documentId, // Include document ID
            letterSuffix: letterSuffix,
            fullChunkId: fullChunkId,
        });
    });

    // Replace citation markers in content
    const processedContent = replaceCitationMarkers(content, citationToDoc);

    return {
        processedContent: processedContent,
        documentBibliography: Array.from(documentMap.values())
    };
}

function generateDocumentId(documentInfo, questionNumber) {
    // Generate a unique document ID based on available identifiers and question number
    let baseId;
    if (documentInfo.doi) {
        baseId = `doi-${documentInfo.doi.replace(/[^a-zA-Z0-9]/g, '-')}`;
    } else if (documentInfo.halid) {
        baseId = `hal-${documentInfo.halid.replace(/[^a-zA-Z0-9]/g, '-')}`;
    } else {
        // Fallback to title-based ID
        const titleId = documentInfo.title
            .toLowerCase()
            .replace(/[^a-zA-Z0-9\s]/g, '')
            .replace(/\s+/g, '-')
            .substring(0, 50);
        baseId = `doc-${titleId}`;
    }

    // Add question number to make it unique per question
    return `${baseId}-${questionNumber}`;
}

function extractDocumentInfo(metadata, payload) {
    return {
        title: metadata.title || payload.title || 'No title (sorry, we are working on it.).',
        description: metadata.description || '', // NEW: Extract description for tooltips
        doi: metadata.doi || '',
        halid: metadata.hal_id || '',
        authors: metadata.authors || [],
        year: metadata.publication_date ? new Date(metadata.publication_date).getFullYear() : ''
    };
}

function replaceCitationMarkers(content, citationToDoc) {
    let processedContent = content;

    citationToDoc.forEach((docInfo, citationId) => {
        const oldMark = `[${citationId}]`;
        const newMark = `<a class="citation-bracket"
                              href="#cite-${docInfo.documentId}"
                              data-chunk-id="${escapeQuotes(docInfo.fullChunkId)}"
                              onmouseover="showChunkTooltip(event, this)"
                              onmouseout="hideChunkTooltip()"
                              style="cursor: help; color: #2563eb; font-weight: 500; transition: color 0.2s;">[${docInfo.docNumber}${docInfo.letterSuffix}]</a>`;
        processedContent = processedContent.replace(new RegExp(`\\[${citationId}\\]`, 'g'), newMark);
    });

    return processedContent;
}

// ==========================================
// BIBLIOGRAPHY DISPLAY
// ==========================================
function addVancouverCitations(messageElement, documentBibliography) {
    const citationsContainer = messageElement.querySelector('.citations-container');

    if (documentBibliography && documentBibliography.length > 0) {
        console.log('Processing Vancouver bibliography:', documentBibliography);

        const bibliographyHtml = createBibliographyHtml(documentBibliography);
        citationsContainer.innerHTML = bibliographyHtml;
    }
}

function createBibliographyHtml(documentBibliography) {
    const documentsHtml = documentBibliography.map(doc => createDocumentHtml(doc)).join('');

    return `
        <div class="mt-3 text-sm">
            <div class="font-semibold text-gray-700 mb-2 flex items-center">
                <span class="mr-1">📚</span>
                Bibliographie:
            </div>
            ${documentsHtml}
        </div>
    `;
}

function createDocumentHtml(doc) {
    // Build authors text
    let authorsText = '';
    if (doc.authors.length > 0) {
        authorsText = doc.authors.join(', ');
        if (doc.year) {
            authorsText += ' (' + doc.year + ')';
        }
    }

    const linksHtml = createDocumentLinksHtml(doc);

    // Build the main HTML structure with actual document ID
    let html = `<div class="bg-gray-50 border border-gray-200 rounded-lg p-3 mb-2 hover:bg-gray-100 transition-colors" id="cite-${doc.documentId}">`;
    html += '<div class="flex justify-between items-start mb-2">';
    html += '<div class="flex-1">';

    // Build the title with data attributes
    html += '<h4 class="font-medium text-gray-900 text-sm leading-tight cursor-pointer"';
    html += ' data-doc-title="' + escapeQuotes(doc.title) + '"';
    html += ' data-doc-description="' + escapeQuotes(doc.description) + '"';
    html += ' data-doc-authors="' + escapeQuotes(authorsText) + '"';
    html += ' data-doc-year="' + doc.year + '"';
    html += ' onmouseover="showTooltip(event, this)"';
    html += ' onmouseout="hideTooltip()">';
    html += doc.title;
    html += '</h4>';

    // Add authors paragraph if authors exist
    if (authorsText) {
        html += '<p class="text-xs text-gray-600 mt-1">';
        html += authorsText;
        html += '</p>';
    }

    html += '</div>'; // Close flex-1 div

    // Add document number
    html += '<div class="ml-2 text-xs text-gray-500 font-bold">';
    html += '[' + doc.docNumber + ']';
    html += '</div>';

    html += '</div>'; // Close flex justify-between div

    // Add links section
    html += '<div class="flex flex-wrap gap-2 text-xs">';
    html += linksHtml;
    html += '</div>';

    html += '</div>'; // Close main container div

    return html;
}

function createDocumentLinksHtml(doc) {
    const links = [];

    if (doc.doi) {
        links.push(`
            <a href="https://doi.org/${doc.doi}" target="_blank" class="text-blue-600 hover:text-blue-800 flex items-center">
                <span class="mr-1">🔗</span>
                DOI: ${doc.doi}
            </a>
        `);
    }

    if (doc.halid) {
        links.push(`
            <a href="https://hal.science/${doc.halid}" target="_blank" class="text-blue-600 hover:text-blue-800 flex items-center">
                <span class="mr-1">🔗</span>
                HALId: ${doc.halid}
            </a>
        `);
    }

    return links.join('');
}

function escapeQuotes(str) {
    if (!str) return '';
    return str.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// ==========================================
// TOOLTIP FUNCTIONALITY
// ==========================================

function showTooltip(event, element) {
    const title = element.getAttribute('data-doc-title');
    const description = element.getAttribute('data-doc-description');
    const authors = element.getAttribute('data-doc-authors');
    const year = element.getAttribute('data-doc-year');

    const tooltip = document.createElement('div');
    tooltip.id = 'document-tooltip';
    tooltip.className = 'absolute z-50 bg-gray-800 text-white text-xs rounded py-3 px-4 max-w-lg shadow-lg';
    tooltip.style.left = event.pageX + 10 + 'px';
    tooltip.style.top = event.pageY - 10 + 'px';
    tooltip.style.minWidth = '300px';

    // Build tooltip content with description as primary content
    const tooltipParts = [];

    if (title) tooltipParts.push(`Titre: ${title}`);
    if (description) tooltipParts.push(`Description: ${description}`);
    if (authors) tooltipParts.push(`Auteurs: ${authors}`);
    if (year) tooltipParts.push(`Année: ${year}`);

    const tooltipContent = tooltipParts.join('\n\n');
    tooltip.textContent = tooltipContent;
    tooltip.style.whiteSpace = 'pre-line';

    document.body.appendChild(tooltip);
}

function hideTooltip() {
    const tooltip = document.getElementById('document-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}


// Cache for chunk data to avoid repeated API calls
const chunkCache = new Map();

function showChunkTooltip(event, element) {
    const chunkId = element.getAttribute('data-chunk-id');

    // Create initial tooltip with loading state
    const tooltip = document.createElement('div');
    tooltip.id = 'chunk-tooltip';
    tooltip.className = 'absolute z-50 bg-blue-800 text-white text-xs rounded py-2 px-3 shadow-lg';
    tooltip.style.left = event.pageX + 10 + 'px';
    tooltip.style.top = event.pageY - 10 + 'px';
    tooltip.style.maxWidth = '400px';
    tooltip.style.minWidth = '200px';
    tooltip.style.wordBreak = 'break-word';

    // Show loading state initially
    tooltip.innerHTML = `
        <div class="flex items-center">
            <span class="animate-spin mr-2">⟳</span>
            Loading chunk data...
        </div>
        <div class="text-xs opacity-75 mt-1">ID: ${chunkId}</div>
    `;

    document.body.appendChild(tooltip);

    // Fetch chunk data from server
    fetchChunkData(chunkId, tooltip);
}

async function fetchChunkData(chunkId, tooltip) {
    try {
        // Check cache first
        if (chunkCache.has(chunkId)) {
            displayChunkData(chunkCache.get(chunkId), tooltip, chunkId);
            return;
        }

        // Get API URL from configuration
        const apiUrl = document.getElementById('api-url').value || DEFAULT_HOST;

        // Make API request to retrieve chunk
        const response = await fetch(`${apiUrl}/v3/chunks/${chunkId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        const chunkData = data.results;

        // Cache the result
        chunkCache.set(chunkId, chunkData);

        // Display the data
        displayChunkData(chunkData, tooltip, chunkId);

    } catch (error) {
        console.error('Error fetching chunk data:', error);
        displayChunkError(error, tooltip, chunkId);
    }
}

function displayChunkData(chunkData, tooltip, chunkId) {
    // Build tooltip content from chunk data
    let content = '<div class="space-y-2">';

    // Chunk ID
    content += `<div class="text-xs opacity-75">Chunk ID: ${chunkId}</div>`;

    // Document ID if available
    if (chunkData.document_id) {
        content += `<div class="text-xs opacity-75">Document: ${chunkData.document_id}</div>`;
    }

    // Main text content
    if (chunkData.text) {
        const truncatedText = chunkData.text.length > 600
            ? chunkData.text.substring(0, 600) + '...'
            : chunkData.text;
        content += `<div class="font-medium">${escapeHtml(truncatedText)}</div>`;
    }

    // Metadata if available and interesting
    if (chunkData.metadata && Object.keys(chunkData.metadata).length > 0) {
        content += '<div class="text-xs opacity-75 mt-2">Metadata:</div>';
        const interestingKeys = ['title', 'page', 'section', 'chapter', 'author'];

        for (const key of interestingKeys) {
            if (chunkData.metadata[key]) {
                content += `<div class="text-xs opacity-75">• ${key}: ${escapeHtml(String(chunkData.metadata[key]))}</div>`;
            }
        }
    }

    content += '</div>';

    tooltip.innerHTML = content;
}

function displayChunkError(error, tooltip, chunkId) {
    tooltip.innerHTML = `
        <div class="text-red-200">
            <div class="font-medium">⚠️ Error loading chunk</div>
            <div class="text-xs mt-1">ID: ${chunkId}</div>
            <div class="text-xs mt-1 opacity-75">${escapeHtml(error.message)}</div>
        </div>
    `;

    // Change tooltip color to indicate error
    tooltip.className = tooltip.className.replace('bg-blue-800', 'bg-red-600');
}

function hideChunkTooltip() {
    const tooltip = document.getElementById('chunk-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Utility function to escape HTML in text content
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function clearChunkCache() {
    chunkCache.clear();
    console.log('Chunk cache cleared');
}


// ==========================================
// FEEDBACK BUTTONS
// ==========================================
function addFeedbackButtons(botMessage, requestBody, results) {
    const feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'flex gap-2 mt-2';
    feedbackDiv.innerHTML = `
        <button class="thumb-up text-green-600 hover:text-green-800" title="Bonne réponse.">👍</button>
        <button class="thumb-down text-red-600 hover:text-red-800" title="Réponse insuffisante.">👎</button>
        <a href="${FEEDBACK_HOST}/v1/feedback/view" title="Ouvrir la table des feedbacks.">📊</a>
    `;

    botMessage.querySelector('.message-content').after(feedbackDiv);

    // Add event listeners for feedback buttons
    feedbackDiv.querySelector('.thumb-up').addEventListener('click', () => {
        sendFeedback(requestBody, results, 'up');
        feedbackDiv.remove();
    });

    feedbackDiv.querySelector('.thumb-down').addEventListener('click', () => {
        sendFeedback(requestBody, results, 'down');
        feedbackDiv.remove();
    });
}
