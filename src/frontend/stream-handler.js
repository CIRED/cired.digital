// Modified streaming display functions for paragraph building

function showStreamingEvents() {
    // debugLog('Showing streaming events container');
    progressDialog = document.getElementById('progress-dialog');
    if (progressDialog) { return progressDialog; }
}

function addStreamingEvent(eventType, timestamp, data = null) {
    // Validate inputs
    if (typeof eventType === 'undefined') {
        eventType = 'unknown';
    }

    if (typeof timestamp === 'undefined' || isNaN(timestamp)) {
        timestamp = 0;
    }

    progressDialog = document.getElementById('progress-dialog');
    if (!progressDialog) {
        debugLog('Progress dialog not found');
    }

    // Handle message content differently - build paragraph
    if (eventType === 'message') {
        handleMessageStreaming(progressDialog, timestamp, data);
        return;
    }

    // For non-message events, create individual event lines as before
    const eventDiv = document.createElement('div');
    eventDiv.className = 'streaming-event';

    let eventText = `[${timestamp.toFixed(1)}s] ${eventType}`;

    // Add data preview for certain event types
    if (data && eventType === 'citation') {
        eventText += ': citation added';
    } else if (data && eventType === 'search_results') {
        count = data.data.chunk_search_results.length;
        eventText += `: ${count} results`;
    } else if (data && eventType === 'metadata') {
        eventText += ': metadata updated';
    } else if (data && eventType === 'completion') {
        eventText += ': response complete';
    }

    eventDiv.textContent = eventText;
    progressDialog.appendChild(eventDiv);

    eventDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function handleMessageStreaming(container, timestamp, data) {
    // Extract text content from data
    let messageText = '';

    // Anthropic delta format
    if (data && data.delta && data.delta.content) {
        for (const content of data.delta.content) {
            if (content.type === 'text' && content.payload && content.payload.value) {
                messageText = content.payload.value;
            }
        }
    }
    // Simple data field
    else if (data && data.data) {
        messageText = data.data;
    }
    // Direct string
    else if (typeof data === 'string') {
        messageText = data;
    }
    // Content field
    else if (data && data.content) {
        messageText = data.content;
    }

    if (!messageText) return;

    // Find or create the message paragraph container
    let streamContainer = container.getElementById('streaming-message-container');
    if (!streamContainer) {
        streamContainer = document.createElement('div');
        streamContainer.id = 'streaming-message-container';

        // Add header for the message section
        const messageHeader = document.createElement('div');
        messageHeader.className = 'streaming-event';
        messageHeader.textContent = `[${timestamp.toFixed(1)}s] message: generating response...`;

        // Create the actual text paragraph
        const messageParagraph = document.createElement('div');
        messageParagraph.className = 'streaming-message-text';
        messageParagraph.style.cssText = `
            margin: 8px 0 8px 20px;
            padding: 8px;
            background: rgba(0, 0, 0, 0.05);
            border-radius: 4px;
            font-family: inherit;
            line-height: 1.4;
            white-space: pre-wrap;
            word-wrap: break-word;
        `;

        streamContainer.appendChild(messageHeader);
        streamContainer.appendChild(messageParagraph);
        container.appendChild(streamContainer);
    }

    // Append new text to the paragraph
    const messageParagraph = streamContainer.querySelector('.streaming-message-text');
    if (messageParagraph) {
        messageParagraph.textContent += messageText;

        // Scroll to keep the latest content visible
        messageParagraph.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}


// Stream state management
function createStreamState() {
    return {
        finalAnswer: '',
        citations: [],
        searchResults: [],
        currentEvent: null,
        metadata: {}
    };
}

// Line buffer management
function createLineBuffer() {
    let buffer = '';

    return {
        addChunk(chunk) {
            buffer += chunk;
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            return lines.filter(line => line.trim() !== '');
        },

        processRemaining(streamState, startTime) {
            if (buffer.trim()) {
                debugLog('Processing final buffered content:', buffer.slice(0, 100));
                processLine(buffer.trim(), streamState, startTime);
            }
        }
    };
}

// Process individual line
function processLine(line, streamState, startTime) {
    const trimmedLine = line.trim();
    if (!trimmedLine) return;

    if (trimmedLine.startsWith('event: ')) {
        streamState.currentEvent = trimmedLine.slice(7);
        return;
    }

    if (trimmedLine.startsWith('data: ')) {
        processDataLine(trimmedLine, streamState, startTime);
    }
}

// Process data lines
function processDataLine(line, streamState, startTime) {
    const jsonStr = line.slice(6);

    if (jsonStr === '[DONE]' || jsonStr === 'DONE') {
        debugLog('Stream completion marker received');
        return;
    }

    if (!isValidJsonStart(jsonStr)) {
        debugLog('Skipping invalid JSON start:', jsonStr.slice(0, 50));
        return;
    }

    try {
        const eventData = JSON.parse(jsonStr);
        const timestamp = (Date.now() - startTime) / 1000;

        handleStreamEvent(streamState.currentEvent, eventData, timestamp, streamState);

    } catch (parseError) {
        debugLog('JSON parse error - will retry on next chunk:', {
            error: parseError.message,
            jsonStart: jsonStr.slice(0, 50),
            jsonEnd: jsonStr.slice(-50),
            currentEvent: streamState.currentEvent,
            isIncomplete: !jsonStr.includes('}')
        });
    }
}

// Handle different event types
function handleStreamEvent(eventType, eventData, timestamp, streamState) {
    if (eventType !== 'message') {
        debugLog('Parsed event data:', {
            eventType,
            timestamp,
            dataSize: JSON.stringify(eventData).length
        });
    }

    // Add to streaming display
    addStreamingEvent(eventType, timestamp, eventData);

    // Process event data
    switch (eventType) {
        case 'search_results':
            handleSearchResults(eventData, streamState);
            break;
        case 'message':
            handleMessage(eventData, streamState);
            break;
        case 'citation':
            handleCitation(eventData, streamState);
            break;
        case 'final_answer':
            handleFinalAnswer(eventData, streamState);
            break;
        case 'metadata':
            handleMetadata(eventData, streamState);
            break;
        case 'completion':
        case 'done':
            handleCompletion();
            break;
        default:
            debugLog('Unhandled event type:', eventType);
    }
}

// Event handlers
function handleSearchResults(eventData, streamState) {
    if (eventData.data?.chunk_search_results) {
        streamState.searchResults = eventData.data.chunk_search_results;
        if (eventData.data.metadata) {
            streamState.metadata = eventData.data.metadata;
        }
    } else if (eventData.results?.chunk_search_results) {
        streamState.searchResults = eventData.results.chunk_search_results;
        if (eventData.results.metadata) {
            streamState.metadata = eventData.results.metadata;
        }
    } else if (eventData.chunk_search_results) {
        streamState.searchResults = eventData.chunk_search_results;
    }

    if (eventData.metadata) {
        streamState.metadata = eventData.metadata;
    }

    debugLog('Search results processed:', {
        count: streamState.searchResults.length,
        hasMetadata: !!Object.keys(streamState.metadata).length
    });
}

function handleMessage(eventData, streamState) {
    let messageText = '';

    if (eventData.delta?.content) {
        for (const content of eventData.delta.content) {
            if (content.type === 'text' && content.payload?.value) {
                messageText = content.payload.value;
            }
        }
    } else if (eventData.data) {
        messageText = eventData.data;
    } else if (typeof eventData === 'string') {
        messageText = eventData;
    } else if (eventData.content) {
        messageText = eventData.content;
    }

    if (messageText) {
        streamState.finalAnswer += messageText;
    }
}

function handleCitation(eventData, streamState) {
    if (eventData) {
        const citationData = eventData.data || eventData;
        streamState.citations.push(citationData);
        debugLog('Citation added:', { count: streamState.citations.length });
    }
}

function handleFinalAnswer(eventData, streamState) {
    let finalText = '';
    if (eventData.content) {
        finalText = eventData.content;
    } else if (eventData.data) {
        finalText = eventData.data;
    } else if (typeof eventData === 'string') {
        finalText = eventData;
    }

    if (finalText && finalText.length > streamState.finalAnswer.length) {
        streamState.finalAnswer = finalText;
        debugLog('Final answer set:', { length: streamState.finalAnswer.length });
    }
}

function handleMetadata(eventData, streamState) {
    if (eventData) {
        streamState.metadata = { ...streamState.metadata, ...eventData };
        debugLog('Metadata updated:', streamState.metadata);
    }
}

function handleCompletion() {
    debugLog('Stream completion event received');
    const streamContainer = document.getElementById('streaming-message-container');
    if (streamContainer) {
        const header = streamContainer.querySelector('.streaming-event');
        if (header) {
            header.textContent = header.textContent.replace('generating response...', 'response complete');
        }
    }
}

function createFinalResult(streamState, startTime) {
    const finalResult = {
        results: {
            generated_answer: streamState.finalAnswer || 'No response generated.',
            citations: streamState.citations,
            search_results: streamState.searchResults,
            metadata: Object.keys(streamState.metadata).length > 0 ? streamState.metadata : {
                usage: {
                    prompt_tokens: 0,
                    completion_tokens: streamState.finalAnswer.length || 0,
                    total_tokens: streamState.finalAnswer.length || 0
                }
            }
        },
        duration: Date.now() - startTime
    };

    debugLog('Final response data:', finalResult);
    return finalResult;
}

// Main stream processing function
async function processStream(responseData) {
    const reader = responseData.response.body.getReader();
    const decoder = new TextDecoder();
    const startTime = Date.now();

    const streamState = createStreamState();
    const lineBuffer = createLineBuffer();

    debugLog('Starting stream processing');

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = lineBuffer.addChunk(chunk);

            for (const line of lines) {
                processLine(line, streamState, startTime);
            }
        }

        // Process any remaining buffered content
        lineBuffer.processRemaining(streamState, startTime);

    } finally {
        reader.releaseLock();
    }

    debugLog('Stream processing complete:', {
        finalAnswerLength: streamState.finalAnswer.length,
        citationsCount: streamState.citations.length,
        searchResultsCount: streamState.searchResults.length,
        hasMetadata: !!Object.keys(streamState.metadata).length,
        duration: (Date.now() - startTime) / 1000
    });

    return createFinalResult(streamState, startTime);
}


function isValidJsonStart(jsonStr) {
    const trimmed = jsonStr.trim();
    if (!trimmed) return false;
    if (!trimmed.startsWith('{') && !trimmed.startsWith('[') && !trimmed.startsWith('"')) {
        return false;
    }
    return true;
}
