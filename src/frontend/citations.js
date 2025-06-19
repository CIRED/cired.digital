// ==========================================
// VANCOUVER CITATIONS PROCESSING
// ==========================================

function initializeCitationContext(messageId) {
    const documentMap = new Map();
    const citationToDoc = new Map();
    let docCounter = 1;
    const questionNumber = messageId || `msg-${Date.now()}`;
    return { documentMap, citationToDoc, docCounter, questionNumber };
}

function prepareDocumentEntry(citation, questionNumber) {
    const payload = citation.payload || citation;
    const metadata = payload.metadata || {};
    const docMeta = extractDocumentInfo(metadata, payload);
    const fullChunkId = payload.id || citation.id || '';
    const docKey = payload.document_id || fullChunkId;
    return { docKey, fullChunkId, docMeta };
}

function createDocumentRecord(docMeta, context) {
    const record = {
        docNumber: context.docCounter,
        documentId: generateDocumentId(docMeta, context.questionNumber),
        questionNumber: context.questionNumber,
        ...docMeta,
        citations: [],
        chunkCounter: 0
    };
    context.docCounter++;
    return record;
}

function getNextLetterSuffix(docRecord) {
    docRecord.chunkCounter++;
    return String.fromCharCode(96 + docRecord.chunkCounter);
}

function addCitationToDocument(docRecord, citation, payload, letterSuffix) {
    const citationId = citation.id || payload.id || '';
    docRecord.citations.push({
        id: citationId,
        text: payload.text || citation.text || '',
        score: payload.score || citation.score || 0,
        letterSuffix: letterSuffix
    });
}

function processCitations(citations, messageId = null) {
    debugLog('Processing citations', {
        citationsCount: citations.length,
        messageId
    });

    const context = initializeCitationContext(messageId);

    for (const citation of citations) {
        const { docKey, fullChunkId, docMeta } = prepareDocumentEntry(citation, context.questionNumber);
        const citationId = citation.id || citation.payload?.id || '';
        if (context.citationToDoc.has(citationId)) continue;

        if (!context.documentMap.has(docKey)) {
            context.documentMap.set(docKey, createDocumentRecord(docMeta, context));
        }

        const doc = context.documentMap.get(docKey);
        const letterSuffix = getNextLetterSuffix(doc);
        const payload = citation.payload || citation;

        addCitationToDocument(doc, citation, payload, letterSuffix);

        context.citationToDoc.set(citationId, {
            docNumber: doc.docNumber,
            documentId: doc.documentId,
            letterSuffix: letterSuffix,
            fullChunkId: fullChunkId
        });
    }

    debugLog('Citations processed successfully', {
        documentsCount: context.documentMap.size,
        citationToDocCount: context.citationToDoc.size
    });

    return {
        citationToDoc: context.citationToDoc,
        bibliography: Array.from(context.documentMap.values())
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
 //   debugLog('Debug - extractDocumentInfo - original metadata.authors:', metadata.authors, 'Type:', typeof metadata.authors);

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

//    debugLog('extractDocumentInfo - processed authors:', authors, 'Type:', typeof authors, 'IsArray:', Array.isArray(authors));

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
    debugLog('Replacing citation markers in content', { content, citationToDoc: Array.from(citationToDoc.entries()) });
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

function createBibliographyHtml(documentBibliography) {
    const documentsHtml = documentBibliography.map(doc => createDocumentHtml(doc)).join('');

    return `
        <div class="bibliography-container">
            <div class="bibliography-header">
                Pour en savoir plus:
            </div>
            ${documentsHtml}
        </div>
    `;
}

function createDocumentHtml(doc) {
    const authorsText = sanitizedAuthorsDate(doc.authors, doc.year);
    const linksHtml = createDocumentLinksHtml(doc);
    const chunkList = doc.citations.map(c => `${doc.docNumber}${c.letterSuffix}`).join(', ');

    return `
        <div class="document-item" id="cite-${doc.documentId}">
            <div class="document-number" style="margin-right: 1em;">[${chunkList}]</div>
            <div class="document-content">
                <h4 class="document-title"
                    data-doc-title="${escapeQuotes(doc.title)}"
                    data-doc-description="${escapeQuotes(doc.description)}"
                    data-doc-authors="${escapeQuotes(authorsText)}"
                    data-doc-year="${doc.year}"
                    onmouseover="showTooltip(event, this)"
                    onmouseout="hideTooltip()">
                    ${doc.title}
                </h4>
                ${authorsText ? `<p class="document-authors">${authorsText}</p>` : ''}
                <p class="document-chunks">Chunks: ${chunkList}</p>
                <p class="document-links">${linksHtml}</p>
            </div>
        </div>
    `;
}

function sanitizedAuthorsDate(authors, year) {
    // Build authors line with robust safety checks
    // which should not be necessary, we already check authors in extractDocumentInfo
    //debugLog('Debug - doc.authors:', doc.authors, 'Type:', typeof doc.authors);

    let authorsArray = [];

    if (Array.isArray(authors)) {
        authorsArray = authors;
    } else if (typeof authors === 'string') {
        authorsArray = authors.split(/[,;]/).map(author => author.trim()).filter(author => author.length > 0);
    } else if (authors) {
        authorsArray = [String(authors)];
    }

    // Remove quotes and trim
    authorsArray = authorsArray.map(author =>
        typeof author === 'string'
            ? author.replace(/['"]/g, '').trim()
            : String(author).replace(/['"]/g, '').trim()
    ).filter(author => author.length > 0);

    let authorsText = authorsArray.join(', ');
    if (authorsText && year) {
        authorsText += ' (' + year + ')';
    }
    return authorsText;
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
