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

// ==========================================
// CHUNK TOOLTIP FUNCTIONALITY
// ==========================================
function showChunkTooltip(event, element) {
    const chunkId = element.getAttribute('data-chunk-id');

    debugLog('Showing chunk tooltip', { chunkId });

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
    debugLog('Fetching chunk data from API', { chunkId });

    try {
        // Check cache first
        if (chunkCache.has(chunkId)) {
            debugLog('Using cached chunk data', { chunkId });
            displayChunkData(chunkCache.get(chunkId), tooltip, chunkId);
            return;
        }

        // Get API URL from configuration
        const apiUrl = document.getElementById('api-url').value || DEFAULT_HOST;

        const startTime = Date.now();
        const response = await fetch(`${apiUrl}/v3/chunks/${chunkId}`, {
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
