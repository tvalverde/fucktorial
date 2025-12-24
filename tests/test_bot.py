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
    date = datetime(2025, 10, 13)  # A Monday
    target_row = AsyncMock()

    # --- Mocks for UI elements ---
    # 1. The 'Añadir' button that is ultimately clicked
    add_button_mock = AsyncMock()
    add_button_mock.scroll_into_view_if_needed = AsyncMock()
    add_button_mock.click = AsyncMock()

    # 2. The locator for the 'Añadir' button
    add_shift_locator_mock = AsyncMock()
    add_shift_locator_mock.first = add_button_mock
    add_shift_locator_mock.wait_for = AsyncMock()

    # 3. The container for the shifts section (the expanded row)
    shifts_container_mock = AsyncMock()
    shifts_container_mock.locator = MagicMock(return_value=add_shift_locator_mock)

    # 4. The toggle button on the main row
    toggle_button_mock = AsyncMock()
    toggle_button_mock.click = AsyncMock()

    # 5. Configure the target_row mock to return the right locator for each call
    def target_row_locator_router(selector):
        if "following-sibling" in selector:
            return shifts_container_mock
        if "attendance-row-toggle" in selector:
            return toggle_button_mock
        return AsyncMock()

    target_row.locator = MagicMock(side_effect=target_row_locator_router)

    # 6. Mocks for the modal that appears after clicking 'Añadir'
    inputs_locator = AsyncMock()
    inputs_locator.count = AsyncMock(return_value=2)
    # nth() is a sync method returning a locator, whose fill() method is async
    nth_locator_mock = AsyncMock()
    nth_locator_mock.fill = AsyncMock()
    inputs_locator.nth = MagicMock(return_value=nth_locator_mock)

    apply_button_locator = AsyncMock()
    apply_button_locator.click = AsyncMock()

    modal_wrapper_locator = AsyncMock()
    # The locator is called for inputs and then for the apply button, for each shift.
    modal_wrapper_locator.locator = MagicMock(
        side_effect=[
            inputs_locator,
            apply_button_locator,
            inputs_locator,
            apply_button_locator,
        ]
    )

    # self.page.locator(...).last
    page_level_locator = AsyncMock()
    page_level_locator.last = modal_wrapper_locator
    mock_page.locator.return_value = page_level_locator
    bot.nav.wait_for_selector = AsyncMock()

    # --- Run ---
    await bot._fill_hours_for_day(date, absence_info=None, target_row=target_row)

    # --- Assertions ---
    # It should toggle the row open
    toggle_button_mock.click.assert_awaited_once()
    # It should click the 'add' button twice
    assert add_button_mock.click.await_count == 2
    # It should fill 4 inputs (start/end for 2 shifts)
    assert inputs_locator.nth.return_value.fill.await_count == 4
    # It should click 'apply' twice
    assert apply_button_locator.click.await_count == 2

    fill_calls = inputs_locator.nth.return_value.fill.await_args_list
    assert fill_calls[0].args[0] == "08:30"
    assert fill_calls[1].args[0] == "14:00"
    assert fill_calls[2].args[0] == "15:00"
    assert fill_calls[3].args[0] == "18:00"


async def test_fill_hours_for_friday(bot, mock_page):
    """
    Tests that _fill_hours_for_day tries to fill one shift for a Friday.
    """
    date = datetime(2025, 10, 17)  # A Friday
    target_row = AsyncMock()

    # --- Mocks for UI elements ---
    add_button_mock = AsyncMock()
    add_button_mock.scroll_into_view_if_needed = AsyncMock()
    add_button_mock.click = AsyncMock()

    add_shift_locator_mock = AsyncMock()
    add_shift_locator_mock.first = add_button_mock
    add_shift_locator_mock.wait_for = AsyncMock()

    shifts_container_mock = AsyncMock()
    shifts_container_mock.locator = MagicMock(return_value=add_shift_locator_mock)

    toggle_button_mock = AsyncMock()
    toggle_button_mock.click = AsyncMock()

    def target_row_locator_router(selector):
        if "following-sibling" in selector:
            return shifts_container_mock
        if "attendance-row-toggle" in selector:
            return toggle_button_mock
        return AsyncMock()

    target_row.locator = MagicMock(side_effect=target_row_locator_router)

    # Mocks for the modal
    inputs_locator = AsyncMock()
    inputs_locator.count = AsyncMock(return_value=2)
    # nth() is a sync method returning a locator, whose fill() method is async
    nth_locator_mock = AsyncMock()
    nth_locator_mock.fill = AsyncMock()
    inputs_locator.nth = MagicMock(return_value=nth_locator_mock)

    apply_button_locator = AsyncMock()
    apply_button_locator.click = AsyncMock()

    modal_wrapper_locator = AsyncMock()
    modal_wrapper_locator.locator = MagicMock(
        side_effect=[inputs_locator, apply_button_locator]
    )

    page_level_locator = AsyncMock()
    page_level_locator.last = modal_wrapper_locator
    mock_page.locator.return_value = page_level_locator
    bot.nav.wait_for_selector = AsyncMock()

    # --- Run ---
    await bot._fill_hours_for_day(date, absence_info=None, target_row=target_row)

    # --- Assertions ---
    toggle_button_mock.click.assert_awaited_once()
    assert add_button_mock.click.await_count == 1
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


@patch("src.bot.FactorialBot._fill_hours_for_day", new_callable=AsyncMock)
async def test_process_attendance_fills_normal_day(
    mock_fill_hours, dry_run_bot, mock_page
):
    dry_run_bot.dry_run = False
    start_date = datetime(2025, 10, 13)
    end_date = datetime(2025, 10, 13)
    mock_row = MagicMock()
    mock_row.text_content = AsyncMock(return_value="13 Oct 0h 00m")

    toggle_button_mock = AsyncMock()
    mock_row.locator.return_value = toggle_button_mock

    rows_locator = MagicMock()
    rows_locator.count = AsyncMock(return_value=1)
    rows_locator.nth.return_value = mock_row

    mock_page.locator.return_value = rows_locator
    mock_page.is_visible = AsyncMock(return_value=False)

    await dry_run_bot.process_attendance(start_date, end_date, absences={})

    toggle_button_mock.click.assert_awaited_once()
    mock_fill_hours.assert_awaited_once_with(start_date, None, mock_row)
