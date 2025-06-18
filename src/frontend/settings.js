window.allAppSettings = {
  dev: {
    apiUrl: "http://localhost:7272",
    models: [
      {
        value: "ollama/mistral-small:24b-3.1-instruct-2503-q8_0",
        label: "Mistral small on CNRS servers"
      },
      {
        value: "ollama/mistral-large:latest",
        label: "Mistral large on CNRS servers"
      },
      {
        value: "ollama/qwen3:32b",
        label: "Qwen 3 32B on CNRS servers"
      },
      {
        value: "deepseek/deepseek-chat",
        label: "Deepseek chat at Deepseek"
      },
      {
        value: "deepseek/deepseek-reasoner",
        label: "Deepseek reasoner at Deepseek"
      },
      {
        value: "mistral/mistral-small-latest",
        label: "Mistral small latest at Mistral"
      },
      {
        value: "mistral/mistral-medium-latest",
        label: "Mistral medium latest at Mistral"
      },
      {
        value: "anthropic/claude-3-5-haiku-latest",
        label: "Claude Haiku 3.5 latest at Anthropic"
      },
      {
        value: "anthropic/claude-sonnet-4-20250514",
        label: "Claude Sonnet 2025-05-14 at Anthropic"
      },
      {
        value: "openai/gpt-4o-mini",
        label: "GPT-4o mini at OpenAI",
        selected: true
      },
      {
        value: "openai/gpt-4.1-mini",
        label: "GPT-4.1 Mini at OpenAI"
      }
    ]
  },
  prod: {
    apiUrl: "http://cired.digital:7272",
    models: [
      {
        value: "ollama/mistral-small:24b-3.1-instruct-2503-q8_0",
        label: "Mistral small on CNRS servers"
      },
      {
        value: "ollama/mistral-large:latest",
        label: "Mistral large on CNRS servers"
      },
      {
        value: "ollama/qwen3:32b",
        label: "Qwen 3 32B on CNRS servers"
      },
      {
        value: "mistral/mistral-small-latest",
        label: "Mistral small latest at Mistral"
      },
      {
        value: "mistral/mistral-medium-latest",
        label: "Mistral medium latest at Mistral"
      }
    ]
  }
};
