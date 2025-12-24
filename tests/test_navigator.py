import pytest
from unittest.mock import MagicMock, AsyncMock
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from src.navigator import Navigator

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.anyio


@pytest.fixture
def mock_page():
    """Provides a mock Page object for testing the navigator."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.click = AsyncMock()
    page.fill = AsyncMock()
    page.text_content = AsyncMock(return_value="some text")
    page.is_visible = AsyncMock(return_value=True)
    return page


@pytest.fixture
def navigator(mock_page):
    """Provides a Navigator instance with a mock page."""
    return Navigator(mock_page)


async def test_goto_success(navigator, mock_page):
    """Tests that goto calls the underlying page methods."""
    test_url = "https://example.com"
    await navigator.goto(test_url)
    mock_page.goto.assert_awaited_with(test_url)
    mock_page.wait_for_load_state.assert_awaited_with("networkidle")


async def test_safe_click_success(navigator, mock_page):
    """Tests a successful safe_click call."""
    selector = "#my-button"
    await navigator.safe_click(selector)
    mock_page.wait_for_selector.assert_awaited_with(
        selector, state="visible", timeout=5000
    )
    mock_page.click.assert_awaited_with(selector)


async def test_safe_click_timeout_raises_exception(navigator, mock_page):
    """Tests that safe_click raises an exception on timeout."""
    selector = "#not-found"
    mock_page.wait_for_selector.side_effect = PlaywrightTimeoutError("test timeout")

    with pytest.raises(PlaywrightTimeoutError, match="test timeout"):
        await navigator.safe_click(selector)


async def test_fill_input_success(navigator, mock_page):
    """Tests a successful fill_input call."""
    selector = "input#name"
    value = "test value"
    await navigator.fill_input(selector, value)
    mock_page.wait_for_selector.assert_awaited_with(
        selector, state="visible", timeout=5000
    )
    mock_page.fill.assert_awaited_with(selector, value)


async def test_get_text_success(navigator, mock_page):
    """Tests a successful get_text call."""
    selector = "p.content"
    result = await navigator.get_text(selector)
    mock_page.wait_for_selector.assert_awaited_with(
        selector, state="visible", timeout=5000
    )
    mock_page.text_content.assert_awaited_with(selector)
    assert result == "some text"


async def test_is_visible(navigator, mock_page):
    """Tests the is_visible call."""
    selector = "div#main"
    result = await navigator.is_visible(selector)
    mock_page.is_visible.assert_awaited_with(selector)
    assert result is True
