// ==========================================
// CITATION PROCESSING WITH MESSAGE CONTEXT
// ==========================================
function processMessageWithCitations(content, citations, messageElement) {
    debugLog('Processing message citations', {
        contentLength: content.length,
        citationsCount: citations.length
    });

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
// VANCOUVER CITATIONS PROCESSING
// ==========================================
function processVancouverCitations(content, citations, messageId = null) {
    debugLog('Processing Vancouver citations', {
        citationsCount: citations.length,
        messageId
    });

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
                documentId: generateDocumentId(documentInfo, questionNumber),
                questionNumber: questionNumber,
                ...documentInfo,
                citations: [],
                chunkCounter: 0
            });
        }

        const doc = documentMap.get(docKey);
        const citationId = citation.id || payload.id || '';
        const fullChunkId = payload.id || citation.id || '';

        // Increment chunk counter and generate letter suffix
        doc.chunkCounter++;
        const letterSuffix = String.fromCharCode(96 + doc.chunkCounter);

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
            documentId: doc.documentId,
            letterSuffix: letterSuffix,
            fullChunkId: fullChunkId,
        });
    });

    // Replace citation markers in content
    const processedContent = replaceCitationMarkers(content, citationToDoc);

    debugLog('Citations processed successfully', {
        documentsCount: documentMap.size,
        processedContentLength: processedContent.length
    });

    return {
        processedContent: processedContent,
        documentBibliography: Array.from(documentMap.values())
    };
}

function generateDocumentId(documentInfo, questionNumber) {
    let baseId;
    if (documentInfo.doi) {
        baseId = `doi-${documentInfo.doi.replace(/[^a-zA-Z0-9]/g, '-')}`;
    } else if (documentInfo.halid) {
        baseId = `hal-${documentInfo.halid.replace(/[^a-zA-Z0-9]/g, '-')}`;
    } else {
        const titleId = documentInfo.title
            .toLowerCase()
            .replace(/[^a-zA-Z0-9\s]/g, '')
            .replace(/\s+/g, '-')
            .substring(0, 50);
        baseId = `doc-${titleId}`;
    }

    return `${baseId}-${questionNumber}`;
}

function extractDocumentInfo(metadata, payload) {
    return {
        title: metadata.title || payload.title || 'No title (sorry, we are working on it.).',
        description: metadata.description || '',
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
    debugLog('Adding Vancouver citations to message', {
        bibliographyCount: documentBibliography?.length || 0
    });

    const citationsContainer = messageElement.querySelector('.citations-container');

    if (documentBibliography && documentBibliography.length > 0) {
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

    // Build the main HTML structure
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

    html += '</div>';
    html += '<div class="ml-2 text-xs text-gray-500 font-bold">';
    html += '[' + doc.docNumber + ']';
    html += '</div>';
    html += '</div>';
    html += '<div class="flex flex-wrap gap-2 text-xs">';
    html += linksHtml;
    html += '</div>';
    html += '</div>';

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

// Cache for chunk data to avoid repeated API calls
const chunkCache = new Map();

function clearChunkCache() {
    chunkCache.clear();
    debugLog('Chunk cache cleared');
}
