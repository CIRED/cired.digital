window.allSettings = {
  dev: {
    apiUrl: "http://localhost:7272",
    debugMode: true,
    models: [
      {
        value: "ollama/mistral-small:24b-3.1-instruct-2503-q8_0",
        label: "Mistral small on CNRS servers",
        defaultTemperature: 0.2
      },
      {
        value: "ollama/mistral-large:latest",
        label: "Mistral large on CNRS servers",
        defaultTemperature: 0.2
      },
      {
        value: "ollama/qwen3:32b",
        label: "Qwen 3 32B on CNRS servers",
        defaultTemperature: 0.6
      },
      {
        value: "deepseek/deepseek-chat",
        label: "Deepseek chat at Deepseek",
        defaultTemperature: 0.6
      },
      {
        value: "deepseek/deepseek-reasoner",
        label: "Deepseek reasoner at Deepseek",
        defaultTemperature: 0.6
      },
      {
        value: "mistral/mistral-small-latest",
        label: "Mistral small latest at Mistral",
        defaultTemperature: 0.2
      },
      {
        value: "mistral/mistral-medium-latest",
        label: "Mistral medium latest at Mistral",
        defaultTemperature: 0.2
      },
      {
        value: "anthropic/claude-3-5-haiku-latest",
        label: "Claude Haiku 3.5 latest at Anthropic",
        defaultTemperature: 0.25
      },
      {
        value: "anthropic/claude-sonnet-4-20250514",
        label: "Claude Sonnet 2025-05-14 at Anthropic",
        defaultTemperature: 0.25
      },
      {
        value: "openai/gpt-4o-mini",
        label: "GPT-4o mini at OpenAI",
        defaultTemperature: 0.2,
        selected: true
      },
      {
        value: "openai/gpt-4.1-mini",
        label: "GPT-4.1 Mini at OpenAI",
        defaultTemperature: 0.2
      }
    ]
  },
  prod: {
    apiUrl: "http://cired.digital:7272",
    debugMode: false,
    models: [
      {
        value: "ollama/mistral-small:24b-3.1-instruct-2503-q8_0",
        label: "Mistral small on CNRS servers",
        defaultTemperature: 0.2
      },
      {
        value: "ollama/mistral-large:latest",
        label: "Mistral large on CNRS servers",
        defaultTemperature: 0.2
      },
      {
        value: "ollama/qwen3:32b",
        label: "Qwen 3 32B on CNRS servers",
        defaultTemperature: 0.6
      },
      {
        value: "mistral/mistral-small-latest",
        label: "Mistral small latest at Mistral",
        defaultTemperature: 0.2
      },
      {
        value: "mistral/mistral-medium-latest",
        label: "Mistral medium latest at Mistral",
        defaultTemperature: 0.2
      }
    ]
  }
};
