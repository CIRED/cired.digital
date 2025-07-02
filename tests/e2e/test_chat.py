"""Tests e2e pour l'interface de chat en production."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_chat_interface_present(page: Page, base_url: str):
    """Test that chat interface elements are present."""
    page.goto(base_url)

    # Wait for SPA to fully load
    page.wait_for_load_state("networkidle")

    # Check for the specific chat input and send button
    chat_input = page.locator("#user-input")
    send_button = page.locator("#send-btn")

    # Verify both elements are present and visible
    expect(chat_input).to_be_visible()
    expect(chat_input).to_be_enabled()

    expect(send_button).to_be_visible()
    expect(send_button).to_be_enabled()

    # Verify the input has the expected placeholder
    expect(chat_input).to_have_attribute(
        "placeholder", "Cirdi, que disent les écrits du CIRED sur..."
    )

    print("Chat interface elements found and visible")


@pytest.mark.smoke
@pytest.mark.e2e
def test_basic_chat_functionality(page: Page, base_url: str):
    """Test sending a message and receiving a response."""
    page.goto(base_url)

    # Wait for the page to be fully loaded
    page.wait_for_load_state("networkidle")

    # Close the onboarding panel
    onboarding_close_btn = page.locator("#onboarding-close-btn")
    onboarding_close_btn.click()

    # Find the specific chat input and send button
    chat_input = page.locator("#user-input")
    send_button = page.locator("#send-btn")

    # Test sending a simple question
    test_message = "Qu'est-ce que le CIRED ?"

    # Clear any existing content and fill the input
    chat_input.clear()
    chat_input.fill(test_message)

    # Verify the text was entered
    filled_value = chat_input.input_value()
    assert test_message in filled_value, (
        f"Text was not properly entered. Expected: {test_message}, Got: {filled_value}"
    )

    # Store initial content for comparison
    initial_content = page.text_content("body") or ""
    initial_length = len(initial_content)

    send_button.click()

    # Verify that the #progress-dialog modal appears and is visible
    expect(page.locator("#progress-dialog")).to_be_visible(timeout=5000)
    print("Progress dialog is visible")

    # Verify that "Recherche dans la base documentaire" appears
    expect(page.locator("text=Recherche dans la base documentaire")).to_be_visible(
        timeout=1000
    )

    # Verify that "Recherche documentaire terminée" appears
    expect(page.locator("text=Recherche documentaire terminée")).to_be_visible(
        timeout=10000
    )
    print("Recherche documentaire termineée")

    # Verify that "Génération de la réponse" appears
    expect(page.locator("text=Génération de la réponse")).to_be_visible(timeout=1000)
    print("Génération de la réponse en cours")

    # Wait for response - look for new content in the messages container
    messages_container = page.locator("#messages-container")
    current_messages = messages_container.text_content() or ""
    print(f"Current messages container content length: {len(current_messages)}")

    try:
        # Wait for content to change significantly
        page.wait_for_function(
            f"document.getElementById('messages-container').textContent.length > {len(messages_container.text_content() or '') + 50}",
            timeout=30000,  # Give more time for the AI response
        )
        print("Response detected in messages container")
        page.screenshot(path="test_success_screenshot.png")
    except Exception as e:
        print(f"Waiting for response failed: {e}")
        # Take a screenshot for debugging
        page.screenshot(path="test_failure_screenshot.png")

    ## Click the close button to dismiss the progress dialog
    close_button = page.locator("#progress-close-btn")
    expect(close_button).to_be_visible(timeout=5000)
    close_button.click()
    print("Progress dialog closed")

    page.screenshot(path="test_success2_screenshot.png")

    # Verify response appeared
    final_content = page.text_content("body") or ""
    content_increase = len(final_content) - initial_length

    print(f"Content length change: {content_increase} characters")

    # Check if there's meaningful content increase
    assert content_increase > 20, (
        f"Insufficient response content detected. Initial: {initial_length}, Final: {len(final_content)}, Increase: {content_increase}"
    )

    print("Chat functionality test completed successfully")


@pytest.mark.e2e
def test_feedback_buttons_interaction(page: Page, base_url: str):
    """Test thumbs up/down feedback functionality."""
    page.goto(base_url)
    page.wait_for_load_state("networkidle")

    # First, we need to send a message to get a response with feedback buttons
    chat_input = page.locator("#user-input")
    send_button = page.locator("#send-btn")

    # Send a simple question
    test_message = "Le changement climatique, qu'est-ce que c'est ?"
    chat_input.fill(test_message)

    send_button.click()

    # Wait for response to appear
    try:
        page.wait_for_function(
            "document.getElementById('messages-container').textContent.length > 1000",
            timeout=30000,
        )
    except Exception:
        print(
            "Warning: Response may not have appeared, continuing to check for feedback buttons"
        )

    ## Click the close button to dismiss the progress dialog
    close_button = page.locator("#progress-close-btn")
    expect(close_button).to_be_visible(timeout=5000)
    close_button.click()
    print("Progress dialog closed")

    # Find thumbs up and thumbs down buttons specifically within messages container
    thumbs_up_button = page.locator("#messages-container").locator("text=👍")
    thumbs_down_button = page.locator("#messages-container").locator("text=👎")

    # Verify both buttons are present and visible
    expect(thumbs_up_button).to_be_visible(timeout=5000)
    expect(thumbs_down_button).to_be_visible(timeout=5000)
    print("Feedback buttons (👍 and 👎) found and visible")

    # Click the thumbs up button
    thumbs_up_button.click()
    print("Clicked thumbs up button")

    # Verify that "Merci pour votre retour" appears
    expect(page.locator("text=Merci pour votre retour")).to_be_visible(timeout=5000)
    print(
        "Feedback confirmation message 'Merci pour votre retour' appeared successfully"
    )
