import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
from playwright.async_api import Page
from src.navigator import Navigator
from src.constants import *

# e.g., {"2025-05-08": {"type": "full", "reason": "sick_leave"}}
AbsenceInfo = Dict[str, str]
Absences = Dict[str, AbsenceInfo]

SPANISH_MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
}

class FactorialBot:
    def __init__(self, page: Page, dry_run: bool = False):
        self.page = page
        self.nav = Navigator(page)
        self.dry_run = dry_run

    async def run(self):
        # New logic: process the last 30 days
        today = datetime.now()
        end_date = today - timedelta(days=1)
        start_date = today - timedelta(days=30)
        
        print(f"Processing range: {start_date.date()} to {end_date.date()}")
        
        absences = await self.detect_absences(start_date, end_date)
        
        await self.process_attendance(start_date, end_date, absences)

    async def detect_absences(self, start_date: datetime, end_date: datetime) -> Absences:
        print("Detecting absences...")
        await self.nav.goto(URL_TIMEOFF)
        
        try:
            await self.page.wait_for_selector("ul.htyto0", timeout=10000)
        except Exception:
            print("Could not find calendar container on page. Aborting absence detection.")
            return {}

        absences: Absences = {}
        dates_to_check = [(start_date + timedelta(days=i)) for i in range((end_date - start_date).days + 1)]
        
        month_names = {v: k for k, v in SPANISH_MONTHS.items()}

        for date_to_check in dates_to_check:
            month_name = month_names.get(date_to_check.month)
            day_str = str(date_to_check.day)
            date_key = date_to_check.strftime("%Y-%m-%d")

            if not month_name:
                continue

            try:
                month_name_element = self.page.locator(f"{SELECTOR_TIMEOFF_MONTH_NAME}:text('{month_name}')")
                if await month_name_element.count() == 0:
                    continue

                month_container = month_name_element.locator("xpath=..")
                
                await month_container.scroll_into_view_if_needed()
                
                day_cell = month_container.locator(f"{SELECTOR_TIMEOFF_DAY_CELL}:text-matches('^{day_str}$')")
                
                if await day_cell.count() == 0:
                    continue

                # First, check for absences indicated by inline background-color
                style = (await day_cell.first.get_attribute("style")) or ""
                reason = None
                if COLOR_VACACIONES in style:
                    reason = "vacation"
                elif COLOR_BAJA in style:
                    reason = "sick_leave"
                elif COLOR_OTRO in style:
                    reason = "other"

                # If no style-based reason, check for class-based holiday
                if not reason:
                    day_class = (await day_cell.first.get_attribute("class")) or ""
                    if "htytoi" in day_class:
                        reason = "holiday"

                if reason:
                    # For holidays, it's always a full day off, no need to click
                    if reason == "holiday":
                        print(f"Absence detected on {date_key} (Reason: holiday)")
                        absences[date_key] = {"type": "full", "reason": "holiday"}
                        continue

                    # For other types, click to determine if it's a half-day
                    print(f"Absence detected on {date_key} (Reason: {reason})")
                    await day_cell.first.click()
                    
                    absence_type = "full"
                    try:
                        modal_body_locator = self.page.locator(SELECTOR_TIMEOFF_MODAL_BODY)
                        await modal_body_locator.wait_for(timeout=5000)
                        
                        if await modal_body_locator.locator("span:has-text('1er mitad del día')").is_visible():
                            absence_type = "half_morning"
                        elif await modal_body_locator.locator("span:has-text('2da mitad del día')").is_visible():
                            absence_type = "half_afternoon"
                        
                        print(f"  -> Type: {absence_type}")
                        absences[date_key] = {"type": absence_type, "reason": reason}
                        
                        await self.page.keyboard.press("Escape")
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        print(f"  -> Error reading modal for {date_key}: {e}. Assuming full day.")
                        absences[date_key] = {"type": "full", "reason": reason}

            except Exception as e:
                print(f"Could not process date {date_key}: {e}")

        print(f"Absences detected: {absences}")
        return absences

    async def process_attendance(self, start_date: datetime, end_date: datetime, absences: Absences):
        year = start_date.year
        month = start_date.month
        
        url = f"{URL_ATTENDANCE_BASE}/{year}/{month}/1"
        await self.nav.goto(url)
        
        current_date = start_date
        while current_date <= end_date:
            date_key = current_date.strftime("%Y-%m-%d")
            day_of_week = current_date.weekday()

            if current_date.month != month:
                print(f"Changing month to {current_date.strftime('%B')}")
                month = current_date.month
                year = current_date.year
                url = f"{URL_ATTENDANCE_BASE}/{year}/{month}/1"
                await self.nav.goto(url)

            rows = self.page.locator(SELECTOR_ATTENDANCE_ROW)
            target_row = None
            for i in range(await rows.count()):
                row = rows.nth(i)
                row_text = (await row.text_content()) or ""
                if row_text.strip().startswith(f"{current_date.day} "):
                   target_row = row
                   break
            
            if not target_row:
                print(f"Row not found for {date_key}")
                current_date += timedelta(days=1)
                continue

            if day_of_week >= 5:
                current_date += timedelta(days=1)
                continue

            absence_info = absences.get(date_key)
            if absence_info and absence_info.get("type") == "full":
                print(f"Skipping {date_key} (Full Day Absence: {absence_info.get('reason')})")
                current_date += timedelta(days=1)
                continue

            if "0h 00m" not in (await target_row.text_content()):
                print(f"Skipping {date_key} (Already filled or non-working day)")
                current_date += timedelta(days=1)
                continue

            print(f"Processing {date_key}...")
            if self.dry_run:
                print("  -> Dry run: Skipping click and fill")
                current_date += timedelta(days=1)
                continue

            try:
                await target_row.locator("svg").first.click()
            except Exception as e:
                print(f"  -> Could not click row for {date_key}: {e}")
                current_date += timedelta(days=1)
                continue

            try:
                if await self.page.is_visible(SELECTOR_POPOVER_FESTIVO, timeout=2000):
                    print(f"Skipping {date_key} (Holiday/Festive)")
                    await self.page.keyboard.press("Escape")
                    current_date += timedelta(days=1)
                    continue
            except:
                pass 

            await self._fill_hours_for_day(current_date, absence_info)
            current_date += timedelta(days=1)

    async def _fill_hours_for_day(self, date: datetime, absence_info: Optional[AbsenceInfo]):
        absence_type = absence_info.get("type") if absence_info else None
        is_friday = (date.weekday() == 4)
        
        shifts = []
        if is_friday:
            if absence_type == "half_morning":
                shifts.append(("12:00", "15:00")) 
            elif absence_type == "half_afternoon":
                shifts.append(("08:30", "12:00"))
            else:
                shifts.append(("08:30", "15:00"))
        else:
            add_morning_shift = True
            add_afternoon_shift = True
            
            if absence_type == "half_morning":
                add_morning_shift = False
            elif absence_type == "half_afternoon":
                add_afternoon_shift = False
            
            if add_morning_shift:
                shifts.append(("08:30", "14:00"))
            if add_afternoon_shift:
                shifts.append(("15:00", "18:00"))

        for i, (start, end) in enumerate(shifts):
            if i > 0:
                await asyncio.sleep(1)
                rows = self.page.locator(SELECTOR_ATTENDANCE_ROW)
                target_row = None
                for r_idx in range(await rows.count()):
                    r = rows.nth(r_idx)
                    if (await r.text_content() or "").strip().startswith(f"{date.day} "):
                        target_row = r
                        break
                if target_row:
                    try:
                        await target_row.locator(SELECTOR_ROW_BUTTON_ADD).click()
                    except Exception:
                        await target_row.locator("svg").first.click()
            
            try:
                await self.nav.wait_for_selector(SELECTOR_MODAL_CONTENT_WRAPPER)
                inputs = self.page.locator(SELECTOR_MODAL_INPUT_TIME)
                if await inputs.count() >= 2:
                    await inputs.nth(0).fill(start)
                    await inputs.nth(1).fill(end)
                
                await self.page.locator(f"//button[normalize-space(.)='Aplicar']").click()
                await asyncio.sleep(1)
            except Exception as e:
                print(f"  -> Error filling shift {start}-{end} for {date.date()}: {e}")
                if await self.page.is_visible(SELECTOR_MODAL_CONTENT_WRAPPER):
                    await self.page.keyboard.press("Escape")
