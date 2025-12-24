import argparse
import sys
import asyncio
from playwright.async_api import async_playwright
from src.auth import Authenticator
from src.bot import FactorialBot


async def main_async():
    parser = argparse.ArgumentParser(description="FactorialHR Auto Clock-in Bot")
    parser.add_argument(
        "--execute", action="store_true", help="Execute changes (disable dry-run)"
    )
    parser.add_argument(
        "--force-login", action="store_true", help="Force interactive login"
    )

    args = parser.parse_args()

    dry_run = not args.execute

    print(f"Starting FactorialBot (Dry Run: {dry_run})")

    # 1. Authentication
    try:
        authenticator = Authenticator(force_login=args.force_login)
        auth_file = await authenticator.authenticate()
    except Exception as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)

    # 2. Run Bot
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Or False for debugging
        context = await browser.new_context(storage_state=auth_file)
        page = await context.new_page()

        try:
            bot = FactorialBot(page, dry_run=dry_run)
            await bot.run()
        except Exception as e:
            print(f"Bot execution failed: {e}")
            sys.exit(1)
        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main_async())
