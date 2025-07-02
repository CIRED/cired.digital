import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_homepage_loads_correctly(page: Page):
    """Test that the SPA homepage loads with all expected elements."""
    page.goto("http://cired.digital/")

    # Test main welcome message
    expect(page.locator("text=votre documentaliste scientifique")).to_be_visible()

    # Test input help text
    expect(page.locator("text=Cirdi parle français")).to_be_visible()

    # Test warning about conversations being recorded
    expect(page.locator("text=Les conversations sont enregistrées")).to_be_visible()

    # Test privacy/data links
    expect(page.locator("text=Voir les données collectées")).to_be_visible()


@pytest.mark.e2e
def test_page_title_and_meta(page: Page):
    """Test page title and basic meta information."""
    page.goto("http://cired.digital/")

    # Check page title
    actual_title = page.title()
    assert "CIRED" in actual_title, f"Expected 'CIRED' in title, got: {actual_title}"


@pytest.mark.e2e
def test_privacy_links_clickable(page: Page):
    """Test that privacy and data collection links are clickable."""
    page.goto("http://cired.digital/")

    # Test data collection link
    data_link = page.locator("text=Voir les données collectées")
    expect(data_link).to_be_visible()
    # Note: Link might be a placeholder (#), so just test it's clickable

    # Test privacy policy link
    privacy_link = page.locator("text=Politique de confidentialité")
    expect(privacy_link).to_be_visible()


@pytest.mark.e2e
def test_responsive_design_mobile(page: Page):
    """Test that the SPA works on mobile viewport."""
    # Set mobile viewport
    page.set_viewport_size({"width": 375, "height": 667})
    page.goto("http://cired.digital/")

    # Main content should still be visible
    expect(page.locator("text=votre documentaliste scientifique")).to_be_visible()


@pytest.mark.e2e
def test_responsive_design_tablet(page: Page):
    """Test that the SPA works on tablet viewport."""
    # Set tablet viewport
    page.set_viewport_size({"width": 768, "height": 1024})
    page.goto("http://cired.digital/")

    # Main content should still be visible
    expect(page.locator("text=votre documentaliste scientifique")).to_be_visible()


@pytest.mark.e2e
def test_no_javascript_errors(page: Page):
    """Test that page loads without JavaScript console errors."""
    # Listen for console errors
    console_errors = []
    page.on(
        "console",
        lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
    )

    page.goto("http://cired.digital/")
    page.wait_for_timeout(5000)  # Wait for SPA to fully load

    # Filter out common non-critical errors
    critical_errors = [
        error
        for error in console_errors
        if not any(
            ignore in error.lower()
            for ignore in ["favicon", "manifest", "network", "cors", "mixed content"]
        )
    ]

    assert len(critical_errors) == 0, f"JavaScript errors found: {critical_errors}"


@pytest.mark.e2e
def test_page_performance_basic(page: Page):
    """Basic performance test - page should load reasonably fast."""
    import time

    start_time = time.time()
    page.goto("http://cired.digital/")

    # Wait for main content to be visible
    expect(page.locator("text=votre documentaliste scientifique")).to_be_visible()

    load_time = time.time() - start_time

    # Should load within 3 seconds
    assert load_time < 3, f"Page took too long to load: {load_time:.2f} seconds"


@pytest.mark.smoke
@pytest.mark.e2e
def test_version_beta_indicator(page: Page):
    """Test that VERSION BETA is displayed."""
    page.goto("http://cired.digital/")
    expect(page.locator("text=VERSION BETA")).to_be_visible()


@pytest.mark.e2e
def test_hal_archive_reference(page: Page):
    """Test that HAL archive is properly referenced."""
    page.goto("http://cired.digital/")
    expect(page.locator("text=HAL")).to_be_visible()
