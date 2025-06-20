const allSettings = {
  profiles: {
    dev: {
      apiUrl: "http://localhost:7272",
      debugMode: true,
      chunkLimit: 10,
      searchStrategy: "vanilla",
      includeWebSearch: false,
      models: [
        "ollama/mistral-small:24b-3.1-instruct-2503-q8_0",
        "ollama/mistral-large:latest",
        "ollama/qwen3:32b",
        "deepseek/deepseek-reasoner",
        "mistral/mistral-small-latest",
        "mistral/mistral-medium-latest",
        "anthropic/claude-3-5-haiku-latest",
        "anthropic/claude-sonnet-4-20250514",
        "openai/gpt-4o-mini",
        "openai/gpt-4.1-mini"
      ]
    },
    prod: {
      apiUrl: "http://cired.digital:7272",
      debugMode: false,
      chunkLimit: 10,
      searchStrategy: "vanilla",
      includeWebSearch: false,
      models: [
        "ollama/mistral-small:24b-3.1-instruct-2503-q8_0",
        "ollama/mistral-large:latest",
        "ollama/qwen3:32b",
        "mistral/mistral-small-latest",
        "mistral/mistral-medium-latest"
      ]
    },
  },

  // Prices in $ per 1M tokens as of 2024-10-01, see README.md for URLs
  modelDefaults: {
    "ollama/mistral-small:24b-3.1-instruct-2503-q8_0": {
      label: "Mistral small on CNRS servers",
      defaultTemperature: 0.2,
      defaultMaxTokens: 1024,
      tariff: { input: 0, output: 0 }
    },
    "ollama/mistral-large:latest": {
      label: "Mistral large on CNRS servers",
      defaultTemperature: 0.2,
      defaultMaxTokens: 1024,
      tariff: { input: 0, output: 0 }
    },
    "ollama/qwen3:32b": {
      label: "Qwen 3 32B on CNRS servers",
      defaultTemperature: 0.6,
      defaultMaxTokens: 1024,
      tariff: { input: 0, output: 0 }
    },
    "deepseek/deepseek-chat": {
      label: "Deepseek chat at Deepseek",
      defaultTemperature: 0.6,
      defaultMaxTokens: 1024,
      tariff: { input: 0.27, cached: 0.07, output: 1.1 }
    },
    "deepseek/deepseek-reasoner": {
      label: "Deepseek reasoner at Deepseek",
      defaultTemperature: 0.6,
      defaultMaxTokens: 4096,
      tariff: { input: 0.55, cached: 0.14, output: 2.29 } // Output includes CoT tokens
    },
    "mistral/mistral-small-latest": {
      label: "Mistral small latest at Mistral",
      defaultTemperature: 0.2,
      defaultMaxTokens: 1024,
      tariff: { input: 0.1, output: 0.3 }
    },
    "mistral/mistral-medium-latest": {
      label: "Mistral medium latest at Mistral",
      defaultTemperature: 0.2,
      defaultMaxTokens: 1024,
      tariff: { input: 0.4, output: 2 }
    },
    "anthropic/claude-3-5-haiku-latest": {
      label: "Claude Haiku 3.5 latest at Anthropic",
      defaultTemperature: 0.25,
      defaultMaxTokens: 1024,
      tariff: { input: 0.80, output: 4 }
    },
    "anthropic/claude-sonnet-4-20250514": {
      label: "Claude Sonnet 2025-05-14 at Anthropic",
      defaultTemperature: 0.25,
      defaultMaxTokens: 1024,
      tariff: { input: 3, output: 15 }
    },
    "openai/gpt-4o-mini": {
      label: "GPT-4o mini at OpenAI",
      defaultTemperature: 0.2,
      defaultMaxTokens: 1024,
      selected: true,
      tariff: { input: 0.15, cached: 0.075, output: 0.60 }
    },
    "openai/gpt-4.1-mini": {
      label: "GPT-4.1 Mini at OpenAI",
      defaultTemperature: 0.2,
      defaultMaxTokens: 1024,
      tariff: { input: 0.40, cached: 0.10, output: 1.60 }
    },
    "openai/gpt-4.1": {
      label: "GPT-4.1 at OpenAI",
      defaultTemperature: 0.2,
      defaultMaxTokens: 1024,
      tariff: { input: 2, cached: 0.50, output: 8 }
    }
  },
};
