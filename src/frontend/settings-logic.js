// ==========================================
// ==========================================

// ==========================================
// CONFIGURATION CONSTANTS
// ==========================================
const DEFAULT_HOST = 'http://localhost:7272';

// ==========================================
// ==========================================
let settings;
let debugMode = false;

// ==========================================
// ==========================================

function detectEnvironment() {
  const hostname = window.location.hostname;
  return (!hostname || hostname === "doudou" || hostname === "localhost") ? "dev" : "prod";
}

function validateSettings(env) {
  if (!allSettings) {
    throw new Error("allSettings not found. Make sure settings.js is included before config.js.");
  }
  if (!allSettings.profiles) {
    throw new Error("allSettings.profiles not found. Invalid settings structure.");
  }
  if (!allSettings.profiles[env]) {
    throw new Error(`Settings inconnus pour '${env}'. Available profiles: ${Object.keys(allSettings.profiles).join(', ')}`);
  }
}

function initializeSettings() {
  try {
    const env = detectEnvironment();
    validateSettings(env);
    settings = allSettings.profiles[env];
    return true;
  } catch (err) {
    console.error("Settings initialization failed:", err.message);
    return false;
  }
}

function loadSettings() {
  try {
    if (!settings) throw new Error("Settings not loaded. Make sure settings.js is included before config.js.");
    applySettings(settings);
  } catch (err) {
    addMainError("Failed to load settings: " + err.message);
  }
}

// ==========================================
// ==========================================

function applySettings(settings) {
    // Set API URL
    if (settings.r2rURL && typeof r2rURLInput !== "undefined") {
        r2rURLInput.value = settings.r2rURL;
    }

    if (settings.cirdiURL && typeof cirdiURLInput !== "undefined") {
        cirdiURLInput.value = settings.cirdiURL;
    }

    // Populate language model select options
    if (settings.models && Array.isArray(settings.models) && typeof modelSelect !== "undefined") {
        modelSelect.innerHTML = '';

        // Build model options using the new structure
        settings.models.forEach(modelKey => {
            const modelConfig = allSettings.modelDefaults[modelKey];
            if (modelConfig) {
                const option = document.createElement('option');
                option.value = modelKey;
                option.textContent = modelConfig.label;
                if (modelConfig.selected) option.selected = true;
                if (modelConfig.disabled) option.disabled = true;
                modelSelect.appendChild(option);
            }
        });

        // Set debug mode from settings
        if (typeof debugModeCheckbox !== "undefined" && settings.debugMode !== undefined) {
        debugModeCheckbox.checked = settings.debugMode;
        debugMode = settings.debugMode;
        }

        // Initialize temperature and max tokens according to selected model
        if (typeof temperatureInput !== "undefined" && Array.isArray(settings.models)) {
        const selectedModelKey = modelSelect.value;
        const modelConfig = allSettings.modelDefaults[selectedModelKey];

        if (modelConfig && modelConfig.defaultTemperature !== undefined) {
            temperatureInput.value = modelConfig.defaultTemperature;
        }
        if (typeof maxTokensInput !== "undefined" && modelConfig && modelConfig.defaultMaxTokens !== undefined) {
            maxTokensInput.value = modelConfig.defaultMaxTokens;
        }

        if (chunkLimitInput && settings.chunkLimit !== undefined) {
            chunkLimitInput.value = settings.chunkLimit;
        }
        if (searchStrategySelect && settings.searchStrategy !== undefined) {
            searchStrategySelect.value = settings.searchStrategy;
        }
        if (includeWebSearchCheckbox && settings.includeWebSearch !== undefined) {
            includeWebSearchCheckbox.checked = settings.includeWebSearch;
        }

        setModelTariffDisplay(selectedModelKey);
        }
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
