// Modified streaming display functions for paragraph building

function showStreamingEvents() {
    // debugLog('Showing streaming events container');
    const existingContainer = document.getElementById('streaming-events');
    if (existingContainer) return existingContainer;

    const eventsContainer = document.createElement('div');
    eventsContainer.id = 'streaming-events';
    eventsContainer.className = 'streaming-events';
    eventsContainer.innerHTML = '<div class="streaming-title">Génération de la réponse:</div>';

    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.appendChild(eventsContainer);
    }

    return eventsContainer;
}

function addStreamingEvent(eventType, timestamp, data = null) {
    // Validate inputs
    if (typeof eventType === 'undefined') {
        eventType = 'unknown';
    }

    if (typeof timestamp === 'undefined' || isNaN(timestamp)) {
        timestamp = 0;
    }

    const container = showStreamingEvents();

    // Handle message content differently - build paragraph
    if (eventType === 'message') {
        handleMessageStreaming(container, timestamp, data);
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
    container.appendChild(eventDiv);

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
    let messageContainer = container.querySelector('.streaming-message-container');
    if (!messageContainer) {
        messageContainer = document.createElement('div');
        messageContainer.className = 'streaming-message-container';

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

        messageContainer.appendChild(messageHeader);
        messageContainer.appendChild(messageParagraph);
        container.appendChild(messageContainer);
    }

    // Append new text to the paragraph
    const messageParagraph = messageContainer.querySelector('.streaming-message-text');
    if (messageParagraph) {
        messageParagraph.textContent += messageText;

        // Scroll to keep the latest content visible
        messageParagraph.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}


async function processStream(responseData) {
    const reader = responseData.response.body.getReader();
    const decoder = new TextDecoder();
    const startTime = Date.now();

    let finalAnswer = '';
    let citations = [];
    let searchResults = [];
    let currentEvent = null;
    let metadata = {};

    // Buffer for incomplete lines/JSON
    let lineBuffer = '';

    debugLog('Starting stream processing');

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });

            // Add chunk to buffer and process complete lines
            lineBuffer += chunk;
            const lines = lineBuffer.split('\n');

            // Keep the last potentially incomplete line in buffer
            lineBuffer = lines.pop() || '';

            // Process complete lines
            for (const line of lines) {
                const trimmedLine = line.trim();
                if (trimmedLine === '') continue;

                // Handle event type declaration
                if (trimmedLine.startsWith('event: ')) {
                    currentEvent = trimmedLine.slice(7);
                    // debugLog('Event type detected:', currentEvent);
                    continue;
                }

                // Handle data lines
                if (trimmedLine.startsWith('data: ')) {
                    const jsonStr = trimmedLine.slice(6);

                    // Handle special cases
                    if (jsonStr === '[DONE]' || jsonStr === 'DONE') {
                        debugLog('Stream completion marker received');
                        continue;
                    }

                    // Validate JSON before parsing
                    if (!isValidJsonStart(jsonStr)) {
                        debugLog('Skipping invalid JSON start:', jsonStr.slice(0, 50));
                        continue;
                    }

                    try {
                        const eventData = JSON.parse(jsonStr);
                        const timestamp = (Date.now() - startTime) / 1000;

                        if (currentEvent !== 'message') {
                            debugLog('Parsed event data:', {
                                eventType: currentEvent,
                                timestamp,
                                dataSize: JSON.stringify(eventData).length
                            });
                        }

                        // Add to streaming display - this will now handle paragraph building
                        addStreamingEvent(currentEvent, timestamp, eventData);

                        // Process based on event type (same as before)
                        switch (currentEvent) {
                            case 'search_results':
                                // Extract search results and metadata
                                if (eventData.data) {
                                    if (eventData.data.chunk_search_results) {
                                        searchResults = eventData.data.chunk_search_results;
                                    }
                                    if (eventData.data.metadata) {
                                        metadata = eventData.data.metadata;
                                    }
                                } else if (eventData.results) {
                                    if (eventData.results.chunk_search_results) {
                                        searchResults = eventData.results.chunk_search_results;
                                    }
                                    if (eventData.results.metadata) {
                                        metadata = eventData.results.metadata;
                                    }
                                } else if (eventData.chunk_search_results) {
                                    searchResults = eventData.chunk_search_results;
                                }

                                if (eventData.metadata) {
                                    metadata = eventData.metadata;
                                }

                                debugLog('Search results processed:', {
                                    count: searchResults.length,
                                    hasMetadata: !!Object.keys(metadata).length
                                });
                                break;

                            case 'message':
                                let messageText = '';

                                // Extract message text (same logic as before)
                                if (eventData.delta && eventData.delta.content) {
                                    for (const content of eventData.delta.content) {
                                        if (content.type === 'text' && content.payload && content.payload.value) {
                                            messageText = content.payload.value;
                                        }
                                    }
                                }
                                else if (eventData.data) {
                                    messageText = eventData.data;
                                }
                                else if (typeof eventData === 'string') {
                                    messageText = eventData;
                                }
                                else if (eventData.content) {
                                    messageText = eventData.content;
                                }

                                if (messageText) {
                                    finalAnswer += messageText;
                                    /* debugLog('Message text added:', {
                                        chunk: messageText.slice(0, 20) + '...',
                                        totalLength: finalAnswer.length
                                    }); */
                                }
                                break;

                            case 'citation':
                                if (eventData) {
                                    const citationData = eventData.data || eventData;
                                    citations.push(citationData);
                                    debugLog('Citation added:', { count: citations.length });
                                }
                                break;

                            case 'final_answer':
                                let finalText = '';
                                if (eventData.content) {
                                    finalText = eventData.content;
                                } else if (eventData.data) {
                                    finalText = eventData.data;
                                } else if (typeof eventData === 'string') {
                                    finalText = eventData;
                                }

                                if (finalText && finalText.length > finalAnswer.length) {
                                    finalAnswer = finalText;
                                    debugLog('Final answer set:', { length: finalAnswer.length });
                                }
                                break;

                            case 'metadata':
                                if (eventData) {
                                    metadata = { ...metadata, ...eventData };
                                    debugLog('Metadata updated:', metadata);
                                }
                                break;

                            case 'completion':
                            case 'done':
                                debugLog('Stream completion event received');
                                // Update the message header to show completion
                                const messageContainer = document.querySelector('.streaming-message-container');
                                if (messageContainer) {
                                    const header = messageContainer.querySelector('.streaming-event');
                                    if (header) {
                                        header.textContent = header.textContent.replace('generating response...', 'response complete');
                                    }
                                }
                                break;

                            default:
                                debugLog('Unhandled event type:', currentEvent);
                        }

                    } catch (parseError) {
                        debugLog('JSON parse error - will retry on next chunk:', {
                            error: parseError.message,
                            jsonStart: jsonStr.slice(0, 50),
                            jsonEnd: jsonStr.slice(-50),
                            currentEvent,
                            isIncomplete: !jsonStr.includes('}')
                        });
                    }
                }
            }
        }

        // Process any remaining buffered content
        if (lineBuffer.trim()) {
            debugLog('Processing final buffered content:', lineBuffer.slice(0, 100));
            if (lineBuffer.trim().startsWith('data: ')) {
                const jsonStr = lineBuffer.trim().slice(6);
                if (isValidJsonStart(jsonStr)) {
                    try {
                        const eventData = JSON.parse(jsonStr);
                        debugLog('Parsed final buffered data');
                    } catch (e) {
                        debugLog('Could not parse final buffer:', e.message);
                    }
                }
            }
        }

    } finally {
        reader.releaseLock();
    }

    debugLog('Stream processing complete:', {
        finalAnswerLength: finalAnswer.length,
        citationsCount: citations.length,
        searchResultsCount: searchResults.length,
        hasMetadata: !!Object.keys(metadata).length
    });

    // Create response data with fallback metadata
    const finalResult = {
        results: {
            generated_answer: finalAnswer || 'No response generated.',
            citations: citations,
            search_results: searchResults,
            metadata: Object.keys(metadata).length > 0 ? metadata : {
                usage: {
                    prompt_tokens: 0,
                    completion_tokens: finalAnswer.length || 0,
                    total_tokens: finalAnswer.length || 0
                }
            }
        }
    };

    debugLog('Final response data:', finalResult);
    return finalResult;
}


function isValidJsonStart(jsonStr) {
    const trimmed = jsonStr.trim();
    if (!trimmed) return false;
    if (!trimmed.startsWith('{') && !trimmed.startsWith('[') && !trimmed.startsWith('"')) {
        return false;
    }
    return true;
}
