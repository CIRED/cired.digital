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

  modelDefaults: {
    "ollama/mistral-small:24b-3.1-instruct-2503-q8_0": {
      label: "Mistral small on CNRS servers",
      defaultTemperature: 0.2,
      defaultMaxTokens: 1024
    },
    "ollama/mistral-large:latest": {
      label: "Mistral large on CNRS servers",
      defaultTemperature: 0.2,
      defaultMaxTokens: 1024
    },
    "ollama/qwen3:32b": {
      label: "Qwen 3 32B on CNRS servers",
      defaultTemperature: 0.6,
      defaultMaxTokens: 1024
    },
    "deepseek/deepseek-chat": {
      label: "Deepseek chat at Deepseek",
      defaultTemperature: 0.6,
      defaultMaxTokens: 1024
    },
    "deepseek/deepseek-reasoner": {
      label: "Deepseek reasoner at Deepseek",
      defaultTemperature: 0.6,
      defaultMaxTokens: 4096
    },
    "mistral/mistral-small-latest": {
      label: "Mistral small latest at Mistral",
      defaultTemperature: 0.2,
      defaultMaxTokens: 1024
    },
    "mistral/mistral-medium-latest": {
      label: "Mistral medium latest at Mistral",
      defaultTemperature: 0.2,
      defaultMaxTokens: 1024
    },
    "anthropic/claude-3-5-haiku-latest": {
      label: "Claude Haiku 3.5 latest at Anthropic",
      defaultTemperature: 0.25,
      defaultMaxTokens: 1024
    },
    "anthropic/claude-sonnet-4-20250514": {
      label: "Claude Sonnet 2025-05-14 at Anthropic",
      defaultTemperature: 0.25,
      defaultMaxTokens: 1024
    },
    "openai/gpt-4o-mini": {
      label: "GPT-4o mini at OpenAI",
      defaultTemperature: 0.2,
      defaultMaxTokens: 1024,
      selected: true
    },
    "openai/gpt-4.1-mini": {
      label: "GPT-4.1 Mini at OpenAI",
      defaultTemperature: 0.2,
      defaultMaxTokens: 1024
    }
  },
};
