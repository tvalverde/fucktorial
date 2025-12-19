import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from src.bot import FactorialBot, AbsenceInfo
from src.constants import *

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.anyio

@pytest.fixture
def mock_page():
    """Provides a mock Page object with all necessary async methods."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.locator = MagicMock()
    page.keyboard.press = AsyncMock()
    page.screenshot = AsyncMock()
    page.is_visible = AsyncMock()
    return page

@pytest.fixture
def bot(mock_page):
    """Provides a FactorialBot instance with a mock page."""
    return FactorialBot(mock_page, dry_run=False)

# --- Tests for _fill_hours_for_day ---

async def test_fill_hours_for_normal_day(bot, mock_page):
    """
    Tests that _fill_hours_for_day tries to fill two shifts for a normal workday.
    """
    date = datetime(2025, 10, 13) # A Monday
    
    # --- Mocks ---
    inputs_locator = MagicMock()
    inputs_locator.count = AsyncMock(return_value=2)
    inputs_locator.nth.return_value.fill = AsyncMock()

    apply_button_locator = MagicMock()
    apply_button_locator.click = AsyncMock()

    # Mocks for the second shift logic
    add_button_locator = MagicMock()
    add_button_locator.click = AsyncMock()

    row_mock = MagicMock()
    row_mock.text_content = AsyncMock(return_value="13 Oct")
    row_mock.locator.return_value = add_button_locator

    rows_locator = MagicMock()
    rows_locator.count = AsyncMock(return_value=1)
    rows_locator.nth.return_value = row_mock

    # Main router for page.locator calls
    def locator_router(selector):
        if selector == SELECTOR_MODAL_INPUT_TIME:
            return inputs_locator
        # Use a more specific check for the apply button
        if "button" in str(selector) and "Aplicar" in str(selector):
            return apply_button_locator
        if selector == SELECTOR_ATTENDANCE_ROW:
            return rows_locator
        return MagicMock() # Default for any other locator call
    mock_page.locator.side_effect = locator_router
    
    # --- Run ---
    await bot._fill_hours_for_day(date, absence_info=None)

    # --- Assertions ---
    assert inputs_locator.nth.return_value.fill.await_count == 4
    assert apply_button_locator.click.await_count == 2
    add_button_locator.click.assert_awaited_once()
    
    fill_calls = inputs_locator.nth.return_value.fill.await_args_list
    assert fill_calls[0].args[0] == "08:30"
    assert fill_calls[1].args[0] == "14:00"
    assert fill_calls[2].args[0] == "15:00"
    assert fill_calls[3].args[0] == "18:00"

async def test_fill_hours_for_friday(bot, mock_page):
    """
    Tests that _fill_hours_for_day tries to fill one shift for a Friday.
    """
    date = datetime(2025, 10, 17) # A Friday

    inputs_locator = MagicMock()
    inputs_locator.count = AsyncMock(return_value=2)
    inputs_locator.nth.return_value.fill = AsyncMock()

    apply_button_locator = MagicMock()
    apply_button_locator.click = AsyncMock()

    def locator_router(selector):
        if selector == SELECTOR_MODAL_INPUT_TIME:
            return inputs_locator
        # Use a more specific check for the apply button
        if "button" in str(selector) and "Aplicar" in str(selector):
            return apply_button_locator
        return MagicMock()
    mock_page.locator.side_effect = locator_router

    await bot._fill_hours_for_day(date, absence_info=None)

    assert inputs_locator.nth.return_value.fill.await_count == 2
    assert apply_button_locator.click.await_count == 1
    fill_calls = inputs_locator.nth.return_value.fill.await_args_list
    assert fill_calls[0].args[0] == "08:30"
    assert fill_calls[1].args[0] == "15:00"

# --- Previous tests from test_bot.py ---

@pytest.fixture
def dry_run_bot(mock_page):
    """Provides a FactorialBot instance with dry_run=True."""
    return FactorialBot(mock_page, dry_run=True)

async def test_process_attendance_skips_weekend(dry_run_bot, mock_page):
    start_date = datetime(2025, 10, 18)
    end_date = datetime(2025, 10, 18)
    mock_row = MagicMock()
    mock_row.text_content = AsyncMock(return_value="18 Oct")
    rows_locator = MagicMock()
    rows_locator.count = AsyncMock(return_value=1)
    rows_locator.nth.return_value = mock_row
    mock_page.locator.return_value = rows_locator
    await dry_run_bot.process_attendance(start_date, end_date, {})
    mock_row.locator("svg").first.click.assert_not_called()

@patch('src.bot.FactorialBot._fill_hours_for_day', new_callable=AsyncMock)
async def test_process_attendance_fills_normal_day(mock_fill_hours, dry_run_bot, mock_page):
    dry_run_bot.dry_run = False
    start_date = datetime(2025, 10, 13)
    end_date = datetime(2025, 10, 13)
    mock_row = MagicMock()
    mock_row.text_content = AsyncMock(return_value="13 Oct 0h 00m")
    mock_row.locator.return_value.first.click = AsyncMock()
    rows_locator = MagicMock()
    rows_locator.count = AsyncMock(return_value=1)
    rows_locator.nth.return_value = mock_row
    
    # FIX: Correctly mock is_visible on the page, not as a locator side effect
    mock_page.locator.return_value = rows_locator
    mock_page.is_visible = AsyncMock(return_value=False)

    await dry_run_bot.process_attendance(start_date, end_date, absences={})
    mock_row.locator("svg").first.click.assert_awaited_once()
    mock_fill_hours.assert_awaited_once_with(start_date, None)
