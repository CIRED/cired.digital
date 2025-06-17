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
        const fullChunkId = payload.id || citation.id || '';
        const docKey = fullChunkId;

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
    // Ensure authors is always an array
    let authors = metadata.authors || [];

    // Debug logging
    debugLog('Debug - extractDocumentInfo - original metadata.authors:', metadata.authors, 'Type:', typeof metadata.authors);

    if (typeof authors === 'string') {
        // Check if the string looks like a JSON array
        if (authors.trim().startsWith('[') && authors.trim().endsWith(']')) {
            try {
                // Try to parse as JSON array
                authors = JSON.parse(authors);
            } catch (e) {
                // If JSON parsing fails, try to extract content between brackets
                const match = authors.match(/\[(.*)\]/);
                if (match) {
                    // Extract content inside brackets and split
                    const content = match[1];
                    authors = content.split(/[,;]/).map(author => {
                        // Remove quotes and trim
                        return author.replace(/['"]/g, '').trim();
                    }).filter(author => author.length > 0);
                } else {
                    // Regular string split
                    authors = authors.split(/[,;]/).map(author => author.trim()).filter(author => author.length > 0);
                }
            }
        } else {
            // Regular string, split by common separators
            authors = authors.split(/[,;]/).map(author => author.trim()).filter(author => author.length > 0);
        }
    } else if (!Array.isArray(authors)) {
        // If authors is neither string nor array, default to empty array
        authors = [];
    }

    // Final cleanup: remove any remaining quotes from array elements
    if (Array.isArray(authors)) {
        authors = authors.map(author => {
            if (typeof author === 'string') {
                return author.replace(/['"]/g, '').trim();
            }
            return String(author).replace(/['"]/g, '').trim();
        }).filter(author => author.length > 0);
    }

    debugLog('Debug - extractDocumentInfo - processed authors:', authors, 'Type:', typeof authors, 'IsArray:', Array.isArray(authors));

    return {
        title: metadata.title || payload.title || 'No title (sorry, we are working on it.).',
        description: metadata.description || '',
        doi: metadata.doi || '',
        halid: metadata.hal_id || '',
        authors: authors,
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
        <div class="bibliography-container">
            <div class="bibliography-header">
                <span class="bibliography-icon">📚</span>
                Bibliographie:
            </div>
            ${documentsHtml}
        </div>
    `;
}


function createDocumentHtml(doc) {
    // Build authors text with robust safety checks
    let authorsText = '';

    // Debug logging to understand what we're getting
    debugLog('Debug - doc.authors:', doc.authors, 'Type:', typeof doc.authors);

    if (doc.authors) {
        let authorsArray = [];

        if (Array.isArray(doc.authors)) {
            authorsArray = doc.authors;
        } else if (typeof doc.authors === 'string') {
            // Split string by common separators
            authorsArray = doc.authors.split(/[,;]/).map(author => author.trim()).filter(author => author.length > 0);
        } else {
            // Convert any other type to string and wrap in array
            authorsArray = [String(doc.authors)];
        }

        if (authorsArray.length > 0) {
            authorsText = authorsArray.join(', ');
            if (doc.year) {
                authorsText += ' (' + doc.year + ')';
            }
        }
    }

    const linksHtml = createDocumentLinksHtml(doc);

    // Build the main HTML structure
     let html = `<div class="document-item" id="cite-${doc.documentId}">`;
    html += '<div class="document-header">';
    html += '<div class="document-content">';

    // Build the title with data attributes
    html += '<h4 class="document-title"';
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
        html += '<p class="document-authors">';
        html += authorsText;
        html += '</p>';
    }

    html += '</div>';
    html += '<div class="document-number">';
    html += '[' + doc.docNumber + ']';
    html += '</div>';
    html += '</div>';
    html += '<div class="document-links">';
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
