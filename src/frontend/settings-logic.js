let settings;  // Global settings object, should get rid of this in the future

// ==========================================

function debugModeOn() {
  const debugModeCheckbox = document.getElementById('debug-mode');
  if (!debugModeCheckbox) {
    console.warn("Debug mode checkbox not found. Make sure it exists in the HTML.");
    return false;
  }
  return debugModeCheckbox.checked;
}

function getSettings() {
  const r2rURLInput = document.getElementById('r2r-url');
  const modelSelect = document.getElementById('model-select');
  const temperatureInput = document.getElementById('temperature');
  const maxTokensInput = document.getElementById('max-tokens');
  const chunkLimitInput = document.getElementById('chunk-limit');
  const searchStrategySelect = document.getElementById('search-strategy');
  const includeWebSearchCheckbox = document.getElementById('include-web-search');
  return {
        r2rURL: r2rURLInput.value,
        model: modelSelect.value,
        temperature: parseFloat(temperatureInput.value),
        maxTokens: parseInt(maxTokensInput.value),
        chunkLimit: parseInt(chunkLimitInput.value, 10),
        searchStrategy: searchStrategySelect.value,
        includeWebSearch: includeWebSearchCheckbox.checked
    };
}

// ==========================================

function detectEnvironment() {
  const hostname = window.location.hostname;
  return (!hostname || hostname === "doudou" || hostname === "localhost") ? "dev" : "prod";
}

function selectSettings(env) {
  // allSettings should be defined in settings.js
  if (!allSettings) {
    throw new Error("allSettings not found. Make sure settings.js is included before settings.js.");
  }
  if (!allSettings.profiles) {
    throw new Error("allSettings.profiles not found. Invalid settings structure.");
  }
  if (!allSettings.profiles[env]) {
    throw new Error(`Settings inconnus pour '${env}'. Available profiles: ${Object.keys(allSettings.profiles).join(', ')}`);
  }
  return allSettings.profiles[env];
}

// ===== Settings UI Initialization =====

function populateFormFromSettings(settings) {
  // Set R2R API URL
  const r2rURLInput = document.getElementById('r2r-url');
  if (settings.r2rURL && r2rURLInput) {
    r2rURLInput.value = settings.r2rURL;
  }

  // Populate language model select options
  const modelSelect = document.getElementById('model-select');
  if (settings.models && Array.isArray(settings.models) && modelSelect) {
    modelSelect.innerHTML = '';

    settings.models.forEach(modelKey => {
      const modelConfig = allSettings.modelDefaults[modelKey];
      if (modelConfig) {
        const option = document.createElement('option');
        option.value = modelKey;
        option.textContent = modelConfig.label;
        modelSelect.appendChild(option);
      }
    });
  }

  // Select the first model
  if (modelSelect.options.length > 0 && !modelSelect.value) {
      modelSelect.selectedIndex = 0;
  }
  handleModelChange();

  const chunkLimitInput = document.getElementById('chunk-limit');
  if (chunkLimitInput && settings.chunkLimit !== undefined) {
    chunkLimitInput.value = settings.chunkLimit;
  }

  const searchStrategySelect = document.getElementById('search-strategy');
  if (searchStrategySelect && settings.searchStrategy !== undefined) {
    searchStrategySelect.value = settings.searchStrategy;
  }

  const telemetryCheckbox = document.getElementById('telemetry-mode');
  if (telemetryCheckbox && settings.telemetryMode !== undefined) {
    telemetryCheckbox.checked = settings.telemetryMode;
    overrideTelemetrySettingFromStorage();
  }

  const cirdiURLInput = document.getElementById('cirdi-url');
  if (cirdiURLInput && settings.cirdiURL !== undefined) {
    cirdiURLInput.value = settings.cirdiURL;
  }

  const debugModeCheckbox = document.getElementById('debug-mode');
  if (debugModeCheckbox && settings.debugMode !== undefined) {
    debugModeCheckbox.checked = settings.debugMode;
    debugMode = settings.debugMode;
  }

  const includeWebSearchCheckbox = document.getElementById('include-web-search');
  if (includeWebSearchCheckbox && settings.includeWebSearch !== undefined) {
    includeWebSearchCheckbox.checked = settings.includeWebSearch;
  }
}


// ==========================================
// Event listeners for settings changes
// ==========================================

function setupSettingsListeners() {
  attach('settings-btn', 'click', openSettingsPanel);
  attach('settings-close-btn', 'click', closeSettingsPanel);
  attach('r2r-url', 'change', updateR2RServerStatus);
  attach('model-select', 'change', handleModelChange);
  attach('debug-mode', 'change', handleDebugModeToggle);
  attach('telemetry-mode', 'change', handleTelemetryToggle);
  attach('chunk-limit', 'change', updateStatusDisplay);
  attach('search-strategy', 'change', updateStatusDisplay);
  attach('include-web-search', 'change', updateStatusDisplay);
  attach('refresh-models-btn', 'click', updateModelStatus);
}


function openSettingsPanel() {
  const settingsPanel = document.getElementById('settings-panel');
  if (!settingsPanel) {
    console.error("Configuration panel not found. Make sure settings-panel element exists in the HTML.");
    return;
  }
  settingsPanel.hidden = false;
  updateR2RServerStatus();
  updateCirdiServerStatus();
  const POLL_INTERVAL_MS = 1000;
  statusInterval = setInterval(updateR2RServerStatus, POLL_INTERVAL_MS);
  feedbackInterval = setInterval(updateCirdiServerStatus, POLL_INTERVAL_MS);
}

function closeSettingsPanel() {
  const settingsPanel = document.getElementById('settings-panel');
  if (!settingsPanel) {
    console.error("Configuration panel not found. Make sure settings-panel element exists in the HTML.");
    return;
  }
  settingsPanel.hidden = true;
  clearInterval(statusInterval);
  clearInterval(feedbackInterval);
}

function handleModelChange() {
  const modelSelect = document.getElementById('model-select');
  const temperatureInput = document.getElementById('temperature');
  const maxTokensInput = document.getElementById('max-tokens');

  if (modelSelect && temperatureInput && maxTokensInput) {
    const selectedModelKey = modelSelect.value;
    const modelConfig = allSettings.modelDefaults[selectedModelKey];

    if (modelConfig && modelConfig.defaultTemperature !== undefined) {
      temperatureInput.value = modelConfig.defaultTemperature;
    }
    if (modelConfig && modelConfig.defaultMaxTokens !== undefined) {
      maxTokensInput.value = modelConfig.defaultMaxTokens;
    }
    setModelTariffDisplay(selectedModelKey);

    updateModelStatus();
  }
}

function setModelTariffDisplay(modelKey) {
  const fallback = "NA (unknown)";
  const loading = "...";

  const inputTariffEl = document.getElementById('input-tariff');
  const outputTariffEl = document.getElementById('output-tariff');

  const modelConfig = allSettings.modelDefaults[modelKey];
  const tariff = modelConfig?.tariff;

  if (tariff && inputTariffEl && outputTariffEl) {
    inputTariffEl.textContent = formatTariff(tariff.input, fallback);
    outputTariffEl.textContent = formatTariff(tariff.output, fallback);
  } else {
    if (inputTariffEl) inputTariffEl.textContent = loading;
    if (outputTariffEl) outputTariffEl.textContent = loading;
  }
}

function formatTariff(value, fallback) {
    return typeof value === "number" ? value.toFixed(2) : fallback;
}

function handleDebugModeToggle() {
  const debugModeCheckbox = document.getElementById('debug-mode');
  if (!debugModeCheckbox) return;

  console.log('Debug mode toggled', { enabled: debugModeCheckbox.checked });
}

function handleTelemetryToggle() {
  const telemetryCheckbox = document.getElementById('telemetry-mode');
  if (!telemetryCheckbox) return;

  localStorage.setItem('telemetry-mode', telemetryCheckbox.checked);
  debugLog('Telemetry mode toggled', { enabled: telemetryCheckbox.checked });
}

function overrideTelemetrySettingFromStorage() {
  const storedValue = localStorage.getItem('telemetry-mode');
  if (storedValue === null) return;

  const telemetryCheckbox = document.getElementById('telemetry-mode');
  if (telemetryCheckbox) {
    telemetryCheckbox.checked = storedValue === 'true';
    debugLog('Telemetry mode overridden from storage', { enabled: telemetryCheckbox.checked });
  }
}
