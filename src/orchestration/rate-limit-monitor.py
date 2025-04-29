"""
Rate Limit Monitor Module.

This module provides a command-line interface to monitor and interact with
rate limits for different AI API services like Mistral and OpenAI.
"""

import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from requests import Response, Session
from requests.exceptions import RequestException


class RateLimitMonitor(ABC):
    """Abstract base class for monitoring API rate limits."""

    api_key: str
    api_url: str
    default_model: str
    model: str
    session: Session

    def __init__(self, model: str | None = None, default_model: str = "") -> None:
        """Initialize the monitor with an optional model name and default."""
        self.api_key = ""
        self.api_url = ""
        self.default_model = default_model
        self.model = model or default_model
        self.session = Session()

    @abstractmethod
    def _headers(self) -> dict[str, str]:
        """Return the request headers for the API."""
        pass

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Return the name of the API service."""
        pass

    def _ensure_api_key(self) -> None:
        """Ensure an API key is set, else raise an error."""
        if not self.api_key:
            raise OSError("API key not set.")

    def check_rate_limits(self) -> None:
        """Send a test request to check current rate limits."""
        self._ensure_api_key()
        url = f"{self.api_url}/chat/completions"
        payload = self._default_payload()
        self._make_request(url, payload)

    def trigger_rate_limits(self, num_requests: int = 10) -> None:
        """Send rapid requests to intentionally trigger rate limits."""
        self._ensure_api_key()
        url = f"{self.api_url}/chat/completions"
        payload = self._default_payload()
        print("Sending rapid requests to trigger rate limits...")
        for i in range(num_requests):
            print(f"Request {i+1}/{num_requests}")
            try:
                response = self.session.post(url, headers=self._headers(), json=payload)
                self._print_response(response)
                if response.status_code == 429:
                    print("Rate limit hit!")
                    break
            except RequestException as e:
                print(f"Network error on request {i+1}: {str(e)}")
                break

    def wait_for_reset(self) -> None:
        """Continuously poll until rate limit resets."""
        self._ensure_api_key()
        url = f"{self.api_url}/chat/completions"
        payload = self._default_payload()
        print("Polling every 10 seconds until rate limit resets...")
        attempt = 1
        start_time = datetime.now()
        while True:
            print(f"Attempt {attempt}")
            try:
                response = self.session.post(url, headers=self._headers(), json=payload)
                if response.status_code == 200:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    print(f"Success after {elapsed:.1f} seconds ✅")
                    break
                print(f"Status {response.status_code}, retrying...")
            except RequestException as e:
                print(f"Network error: {str(e)}")
            attempt += 1
            time.sleep(10)

    def _default_payload(self) -> dict[str, Any]:
        """Return the default payload for requests."""
        return {
            "model": self.model,
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 5,
        }

    def _make_request(self, url: str, payload: dict[str, Any]) -> None:
        """Make a request to the API and print the response."""
        try:
            response = self.session.post(url, headers=self._headers(), json=payload)
            self._print_response(response)
        except RequestException as e:
            print(f"Network error: {str(e)}")

    def _print_response(self, response: Response) -> None:
        """Print relevant rate limit-related headers from the response."""
        print(f"Status Code: {response.status_code}")
        for k, v in response.headers.items():
            if any(word in k.lower() for word in ["rate", "limit", "reset"]):
                print(f"{k}: {v}")

    def _select_model(self, models: list[dict[str, Any]], interactive: bool) -> None:
        """Allow user to select a model from a list of models."""
        if interactive:
            for idx, model in enumerate(models, 1):
                print(f"{idx}. {model.get('id', 'Unknown')}")
            choice = input(
                f"Select a model number or press Enter to keep '{self.model}': "
            )
            if choice.isdigit() and 1 <= int(choice) <= len(models):
                self.model = models[int(choice) - 1].get("id", self.model)
        else:
            for model in models:
                print(f"- {model.get('id', 'Unknown')}")


class MistralMonitor(RateLimitMonitor):
    """Monitor implementation for the Mistral API service."""

    def __init__(self, model: str | None = None) -> None:
        """Initialize Mistral monitor with optional model."""
        super().__init__(model, default_model="mistral-small")
        self.api_key = os.environ.get("MISTRAL_API_KEY", "")
        self.api_url = "https://api.mistral.ai/v1"

    def _headers(self) -> dict[str, str]:
        """Return Mistral-specific request headers."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    @property
    def service_name(self) -> str:
        """Return the service name for Mistral."""
        return "Mistral"

    def list_models(self, interactive: bool = False) -> None:
        """List available Mistral models, optionally interactively."""
        self._ensure_api_key()
        url = f"{self.api_url}/models"
        try:
            response = self.session.get(url, headers=self._headers())
            if response.status_code == 200:
                models = response.json().get("data", [])
                self._select_model(models, interactive)
            else:
                print(f"Failed with status {response.status_code}")
        except RequestException as e:
            print(f"Network error: {str(e)}")


class OpenAIMonitor(RateLimitMonitor):
    """Monitor implementation for the OpenAI API service."""

    def __init__(self, model: str | None = None) -> None:
        """Initialize OpenAI monitor with optional model."""
        super().__init__(model, default_model="gpt-4.1-mini")
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.api_url = "https://api.openai.com/v1"

    def _headers(self) -> dict[str, str]:
        """Return OpenAI-specific request headers."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    @property
    def service_name(self) -> str:
        """Return the service name for OpenAI."""
        return "OpenAI"

    def list_models(self, interactive: bool = False) -> None:
        """List available OpenAI models, optionally interactively."""
        self._ensure_api_key()
        url = f"{self.api_url}/models"
        try:
            response = self.session.get(url, headers=self._headers())
            if response.status_code == 200:
                models = response.json().get("data", [])
                self._select_model(models, interactive)
            else:
                print(f"Failed with status {response.status_code}")
        except RequestException as e:
            print(f"Network error: {str(e)}")


def main() -> None:
    """Select a service, a model, and loop CLI commands."""
    print("\n===== Rate Limit Monitor =====")
    print("Select service:")
    print("1. Mistral")
    print("2. OpenAI")
    choice = input("Enter choice (1 or 2): ")

    monitor: RateLimitMonitor | None = None
    if choice == "1":
        monitor = MistralMonitor()
    elif choice == "2":
        monitor = OpenAIMonitor()
    else:
        print("Invalid choice. Exiting.")
        return

    monitor.list_models(interactive=True)

    while True:
        print(f"\nMenu: [{monitor.service_name} | Model: {monitor.model}]")
        print("1. Check current rate limits")
        print("2. Trigger rate limits")
        print("3. Wait for rate limit to reset")
        print("4. Change model")
        print("5. Exit")

        action = input("Choose an action (1-5): ")

        match action:
            case "1":
                monitor.check_rate_limits()
            case "2":
                monitor.trigger_rate_limits()
            case "3":
                monitor.wait_for_reset()
            case "4":
                monitor.list_models(interactive=True)
            case "5":
                print("Goodbye!")
                break
            case _:
                print("Invalid input. Please try again.")


if __name__ == "__main__":
    main()
