import pytest
from unittest.mock import patch, AsyncMock

# Because main.py is a script, we import it in a way that we can patch it
from src import main as main_script

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.anyio

@patch('src.main.FactorialBot')
@patch('src.main.Authenticator')
@patch('src.main.async_playwright')
async def test_main_default_dry_run(mock_playwright, MockAuthenticator, MockFactorialBot, monkeypatch):
    """
    Tests that running main() with no arguments results in a dry run.
    """
    # Simulate no command-line arguments
    monkeypatch.setattr(main_script.sys, 'argv', ['src/main.py'])
    
    # Setup mocks
    mock_auth_instance = MockAuthenticator.return_value
    mock_auth_instance.authenticate = AsyncMock(return_value="fake_auth_file")
    
    mock_bot_instance = MockFactorialBot.return_value
    mock_bot_instance.run = AsyncMock()

    await main_script.main_async()

    # Assert Authenticator was called correctly
    MockAuthenticator.assert_called_once_with(force_login=False)
    mock_auth_instance.authenticate.assert_awaited_once()

    # Assert FactorialBot was called with dry_run=True
    MockFactorialBot.assert_called_once()
    assert MockFactorialBot.call_args.kwargs['dry_run'] is True
    mock_bot_instance.run.assert_awaited_once()


@patch('src.main.FactorialBot')
@patch('src.main.Authenticator')
@patch('src.main.async_playwright')
async def test_main_with_execute_flag(mock_playwright, MockAuthenticator, MockFactorialBot, monkeypatch):
    """
    Tests that the --execute flag sets dry_run to False.
    """
    monkeypatch.setattr(main_script.sys, 'argv', ['src/main.py', '--execute'])
    
    mock_auth_instance = MockAuthenticator.return_value
    mock_auth_instance.authenticate = AsyncMock(return_value="fake_auth_file")
    
    # FIX: The mocked bot instance needs an async 'run' method
    mock_bot_instance = MockFactorialBot.return_value
    mock_bot_instance.run = AsyncMock()

    await main_script.main_async()

    # Assert FactorialBot was called with dry_run=False
    MockFactorialBot.assert_called_once()
    assert MockFactorialBot.call_args.kwargs['dry_run'] is False


@patch('src.main.FactorialBot')
@patch('src.main.Authenticator')
@patch('src.main.async_playwright')
async def test_main_with_force_login_flag(mock_playwright, MockAuthenticator, MockFactorialBot, monkeypatch):
    """
    Tests that the --force-login flag is passed to the Authenticator.
    """
    monkeypatch.setattr(main_script.sys, 'argv', ['src/main.py', '--force-login'])
    
    mock_auth_instance = MockAuthenticator.return_value
    mock_auth_instance.authenticate = AsyncMock(return_value="fake_auth_file")

    # FIX: The mocked bot instance needs an async 'run' method
    mock_bot_instance = MockFactorialBot.return_value
    mock_bot_instance.run = AsyncMock()
    
    await main_script.main_async()

    # Assert Authenticator was initialized with force_login=True
    MockAuthenticator.assert_called_once_with(force_login=True)

@patch('src.main.Authenticator')
@patch('builtins.print')
async def test_main_authentication_failure(mock_print, MockAuthenticator, monkeypatch):
    """
    Tests that the script exits if authentication fails.
    """
    monkeypatch.setattr(main_script.sys, 'argv', ['src/main.py'])
    
    # Simulate authentication raising an exception
    mock_auth_instance = MockAuthenticator.return_value
    mock_auth_instance.authenticate.side_effect = Exception("Test Auth Error")

    with pytest.raises(SystemExit) as e:
        await main_script.main_async()

    # Assert that the script tried to exit
    assert e.type == SystemExit
    assert e.value.code == 1
    # Assert that a relevant error message was printed
    mock_print.assert_any_call("Authentication failed: Test Auth Error")
