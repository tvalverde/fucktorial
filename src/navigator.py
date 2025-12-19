from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError
import asyncio

class Navigator:
    def __init__(self, page: Page):
        self.page = page

    async def goto(self, url: str):
        print(f"Navigating to {url}")
        await self.page.goto(url)
        await self.page.wait_for_load_state("networkidle")

    async def safe_click(self, selector: str, timeout: int = 5000):
        try:
            print(f"Clicking {selector}")
            await self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            await self.page.click(selector)
        except PlaywrightTimeoutError:
            print(f"Error: Element {selector} not found or not visible within {timeout}ms")
            raise

    async def fill_input(self, selector: str, value: str, timeout: int = 5000):
        try:
            print(f"Filling {selector}")
            await self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            await self.page.fill(selector, value)
        except PlaywrightTimeoutError:
            print(f"Error: Element {selector} not found or not visible within {timeout}ms")
            raise
    
    async def get_text(self, selector: str, timeout: int = 5000) -> str:
        try:
            await self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            return await self.page.text_content(selector) or ""
        except PlaywrightTimeoutError:
            print(f"Error: Element {selector} not found for text extraction")
            raise

    async def wait_for_selector(self, selector: str, timeout: int = 5000) -> Locator:
        return await self.page.wait_for_selector(selector, state="visible", timeout=timeout)

    async def is_visible(self, selector: str) -> bool:
        return await self.page.is_visible(selector)
