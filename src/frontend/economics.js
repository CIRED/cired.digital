function presentEconomics(costs) {
    return `
        <span>
            Tokens: ${costs.tokensIn} in, ${costs.tokensOut} out.
            LLM cost: ${costs.llmCost} cent.
            Self hosting cost: ${costs.hostingCost} cent (H100 VPS hourly rate for ${costs.duration}s.).
        </span>
    `.replace(/\s+/g, ' ').trim();
}

function estimateCosts(settings, results, duration) {
    const seconds = duration / 1000; // Convert milliseconds to seconds
    const tokensIn = results.metadata.usage.prompt_tokens || 0;
    const tokensOut = results.metadata.usage.completion_tokens || 0;
    const modelKey = settings.model || 'unknown';
    const modelConfig = allSettings.modelDefaults?.[modelKey];
    const tariff = modelConfig?.tariff;

    let llmCost = "NA";
    let hostingCost = "NA";

    debugLog('Estimating costs', {tokensIn, tokensOut, modelKey, tariff});

    if (tariff && typeof tariff.input === "number" && typeof tariff.output === "number") {
        const mega = 1_000_000; // 1 million tokens
        // Calculate costs in dollars
        llmCost = tariff.input * tokensIn/mega + tariff.output * tokensOut/mega;
        llmCost = llmCost * 100; // Convert dollars to cents
    }

    if (tariff && typeof tariff.hosting === "number") {
        costPerSecond = tariff.hosting / 3600; // Convert hourly rate to per second
        hostingCost = costPerSecond * seconds * 100; // Convert dollars to cents
    }

    return {
        duration: seconds.toFixed(2),
        tokensIn: tokensIn.toLocaleString(),
        tokensOut: tokensOut.toLocaleString(),
        llmCost: typeof llmCost === "number" ? llmCost.toFixed(2) : llmCost,
        hostingCost: typeof hostingCost === "number" ? hostingCost.toFixed(2) : hostingCost,
        modelName: modelKey
    };
}



// Fixed estimateCosts function to handle missing metadata gracefully
function _estimateCosts(settings, results, duration) {
    const usage = results.metadata?.usage || {
        prompt_tokens: 0,
        completion_tokens: results.generated_answer?.length || 0,
        total_tokens: (results.generated_answer?.length || 0)
    };

    debugLog('Estimating costs with usage:', usage);

    // Your existing cost calculation logic here
    // but with fallback values to prevent errors

    return {
        inputTokens: usage.prompt_tokens || 0,
        outputTokens: usage.completion_tokens || 0,
        totalTokens: usage.total_tokens || 0,
        estimatedCost: 0, // Calculate based on your pricing
        duration: duration || 0
    };
}
