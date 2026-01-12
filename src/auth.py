import os
import getpass
import asyncio
from playwright.async_api import async_playwright, Page, BrowserContext
from src.constants import (
    URL_DASHBOARD,
    URL_LOGIN,
    SELECTOR_EMAIL,
    SELECTOR_PASSWORD,
    SELECTOR_SUBMIT,
    SELECTOR_2FA_INPUT,
    AUTH_FILE_PATH,
)
from src.navigator import Navigator


class Authenticator:
    def __init__(self, force_login: bool = False):
        self.force_login = force_login
        self.auth_file = AUTH_FILE_PATH

    async def authenticate(self) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            # Check if auth file exists and try to use it
            context = None
            if os.path.exists(self.auth_file) and not self.force_login:
                print("Loading session from file...")
                context = await browser.new_context(storage_state=self.auth_file)
            else:
                context = await browser.new_context()

            page = await context.new_page()
            nav = Navigator(page)

            print("Validating session...")
            try:
                await nav.goto(URL_DASHBOARD)
            except Exception as e:
                print(f"Navigation failed: {e}")
                # If navigation fails, we might need login

            final_url = page.url
            if URL_LOGIN in final_url or self.force_login:
                print("Session invalid or forced login. Starting interactive login...")
                await context.close()
                await browser.close()
                await self._interactive_login()
            else:
                # If the session is valid but the auth file doesn't exist, save it.
                if not os.path.exists(self.auth_file):
                    print("Session is valid, saving new session state...")
                    await context.storage_state(path=self.auth_file)
                else:
                    print("Session valid.")
                await context.close()
                await browser.close()

        return self.auth_file

    async def _interactive_login(self):
        # Interactive login requires tty, so we might need headless=False if running locally
        # But instructions say: "Si la sesión es inválida, lanzar navegador (headless=True)."
        # And then ask for input in console.

        email = input("Email: ")
        password = getpass.getpass("Password: ")

        async with async_playwright() as p:
            # Re-launch browser for login flow
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            nav = Navigator(page)

            await nav.goto(URL_LOGIN)
            await nav.fill_input(SELECTOR_EMAIL, email)
            await nav.fill_input(SELECTOR_PASSWORD, password)
            await nav.safe_click(SELECTOR_SUBMIT)

            # 2FA Step
            print("Waiting for page to load after credential submission...")
            try:
                # Wait for navigation to complete after submitting credentials
                await page.wait_for_load_state("networkidle", timeout=15000)

                print("Waiting for 2FA input field...")
                await page.wait_for_selector(SELECTOR_2FA_INPUT, timeout=10000)
                code = input("🔐 Introduce el código 2FA de tu app: ")
                await nav.fill_input(SELECTOR_2FA_INPUT, code)
                await nav.safe_click(SELECTOR_SUBMIT)
                # Let's wait for navigation to dashboard
                print("Waiting for navigation to dashboard...")
                await page.wait_for_url("**/dashboard", timeout=60000)
                print("Login successful!")

                # Save storage state
                await context.storage_state(path=self.auth_file)

            except Exception as e:
                print(f"Login failed or timeout: {e}")
                screenshot_path = os.path.join(
                    os.path.dirname(self.auth_file), "login_failure.png"
                )
                print(f"Saving screenshot to {screenshot_path}")
                await page.screenshot(path=screenshot_path)
                raise e
            finally:
                await context.close()
                await browser.close()
