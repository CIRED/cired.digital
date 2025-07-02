"""Tests e2e pour l'interface de chat en production."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_chat_interface_present(page: Page):
    """Test that chat interface elements are present."""
    page.goto("http://cired.digital/")

    # Wait for SPA to fully load
    page.wait_for_timeout(2000)

    # Look for chat input (common selectors for chat inputs)
    chat_selectors = [
        "input[type='text']",
        "textarea",
        "[role='textbox']",
        ".chat-input",
        "#chat-input",
        "input[placeholder*='question']",
        "input[placeholder*='message']",
    ]

    # At least one chat input should be present
    chat_input_found = False
    for selector in chat_selectors:
        if page.locator(selector).count() > 0:
            chat_input_found = True
            break

    assert chat_input_found, "No chat input field found on the page"


@pytest.mark.smoke
@pytest.mark.e2e
def test_basic_chat_functionality(page: Page):
    """Test sending a message and receiving a response."""
    page.goto("http://cired.digital/")

    # Wait for the page to be fully loaded instead of arbitrary timeout
    page.wait_for_load_state("networkidle")

    # Find chat input field with better error handling
    chat_input = None
    selectors = ["input[type='text']", "textarea", "[role='textbox']"]

    for selector in selectors:
        locator = page.locator(selector)
        if locator.count() > 0:
            chat_input = locator.first
            break

    assert chat_input is not None, "Could not find chat input field"

    # Test sending a simple question
    test_message = "Qu'est-ce que le CIRED ?"
    chat_input.fill(test_message)

    # Try to send with better error handling
    try:
        chat_input.press("Enter")
    except Exception as e:
        print(f"Enter key failed, trying send button: {e}")
        send_button = page.locator(
            "button[type='submit'], .send-button, [aria-label*='send']"
        ).first
        expect(send_button).to_be_visible(timeout=5000)
        send_button.click()

    # Wait for response with a more specific condition
    # Instead of arbitrary timeout, wait for content change
    initial_content = page.text_content("body") or ""

    # Wait for content to change (indicating a response)
    page.wait_for_function(
        f"document.body.textContent.length > {len(initial_content) + 10}", timeout=15000
    )

    # Verify response appeared
    final_content = page.text_content("body") or ""
    assert len(final_content) > len(initial_content), "No response content detected"


@pytest.mark.e2e
def test_feedback_buttons_interaction(page: Page):
    """Test thumbs up/down feedback functionality."""
    page.goto("http://cired.digital/")
    page.wait_for_timeout(3000)

    # After sending a message and getting a response, feedback buttons should appear
    # For now, just check if the feedback mechanism is mentioned
    expect(page.locator("text=👍")).to_be_visible()
    expect(page.locator("text=👎")).to_be_visible()
