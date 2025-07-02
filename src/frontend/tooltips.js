// ==========================================
// DOCUMENT TOOLTIP FUNCTIONALITY
// ==========================================
function showTooltip(event, element) {
    const title = element.getAttribute('data-doc-title');
    const description = element.getAttribute('data-doc-description');
    const authors = element.getAttribute('data-doc-authors');
    const year = element.getAttribute('data-doc-year');

    debugLog('Showing document tooltip', { title: title?.substring(0, 50) });

    const tooltip = document.createElement('div');
    tooltip.id = 'document-tooltip';
    tooltip.className = 'document-tooltip';
    tooltip.style.left = event.pageX + 10 + 'px';
    tooltip.style.top = event.pageY - 10 + 'px';

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

// ==========================================
// CHUNK TOOLTIP FUNCTIONALITY
// ==========================================
function showChunkTooltip(event, element) {
    const chunkId = element.getAttribute('data-chunk-id');

    debugLog('Showing chunk tooltip', { chunkId });

    // Create initial tooltip with loading state
    const tooltip = document.createElement('div');
    tooltip.id = 'chunk-tooltip';
    tooltip.className = 'chunk-tooltip';
    tooltip.style.left = event.pageX + 10 + 'px';
    tooltip.style.top = event.pageY - 10 + 'px';

    // Show loading state initially
    tooltip.innerHTML = `
        <div class="tooltip-loading">
            <span class="tooltip-loading-spinner">⟳</span>
            Loading chunk data...
        </div>
        <div class="tooltip-metadata">ID: ${chunkId}</div>
    `;

    document.body.appendChild(tooltip);

    // Fetch chunk data from server
    fetchChunkData(chunkId, tooltip);
}

async function fetchChunkData(chunkId, tooltip) {
    debugLog('Fetching chunk data from API', { chunkId });

    try {
        // Check cache first
        if (chunkCache.has(chunkId)) {
            debugLog('Using cached chunk data', { chunkId });
            displayChunkData(chunkCache.get(chunkId), tooltip, chunkId);
            return;
        }

        // Get API URL from configuration
        const r2rURL = document.getElementById('r2r-url').value || DEFAULT_HOST;

        const startTime = Date.now();
        const response = await fetch(`${r2rURL}/v3/chunks/${chunkId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const responseTime = Date.now() - startTime;

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        const chunkData = data.results;

        debugLog('Chunk data fetched successfully', {
            chunkId,
            responseTime: `${responseTime}ms`,
            hasText: !!chunkData.text
        });

        // Cache the result
        chunkCache.set(chunkId, chunkData);

        // Display the data
        displayChunkData(chunkData, tooltip, chunkId);

    } catch (error) {
        debugLog('Error fetching chunk data', {
            chunkId,
            error: error.message
        });
        displayChunkError(error, tooltip, chunkId);
    }
}

function displayChunkData(chunkData, tooltip, chunkId) {
    // Build tooltip content from chunk data
    let content = '<div>';

    // Chunk ID
    content += `<div class="tooltip-metadata">Chunk ID: ${chunkId}</div>`;

    // Document ID if available
    if (chunkData.document_id) {
        content += `<div class="tooltip-metadata">Document: ${chunkData.document_id}</div>`;
    }

    // Main text content
    if (chunkData.text) {
        content += `<div class="tooltip-content">${escapeHtml(chunkData.text)}</div>`;
    }

    // Metadata if available and interesting
    if (chunkData.metadata && Object.keys(chunkData.metadata).length > 0) {
        content += '<div class="tooltip-metadata tooltip-content">Metadata:</div>';
        const interestingKeys = ['title', 'page', 'section', 'chapter', 'author'];

        for (const key of interestingKeys) {
            if (chunkData.metadata[key]) {
                content += `<div class="tooltip-metadata">• ${key}: ${escapeHtml(String(chunkData.metadata[key]))}</div>`;
            }
        }
    }

    content += '</div>';

    tooltip.innerHTML = content;
}

function displayChunkError(error, tooltip, chunkId) {
    tooltip.innerHTML = `
        <div>
            <div><strong>⚠️ Error loading chunk</strong></div>
            <div class="tooltip-metadata">ID: ${chunkId}</div>
            <div class="tooltip-metadata">${escapeHtml(error.message)}</div>
        </div>
    `;

    // Change tooltip color to indicate error
    tooltip.className = 'chunk-tooltip chunk-tooltip-error';
}

function hideChunkTooltip() {
    const tooltip = document.getElementById('chunk-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}


// Cache for chunk data to avoid repeated API calls
const chunkCache = new Map();

function clearChunkCache() {
    chunkCache.clear();
    debugLog('Chunk cache cleared');
}
