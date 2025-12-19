# URLs
URL_LOGIN = "https://api.factorialhr.com/en/users/sign_in?&return_to=https%3A%2F%2Fapp.factorialhr.com%2F"
URL_DASHBOARD = "https://app.factorialhr.com/"
URL_TIMEOFF = "https://app.factorialhr.com/time-off"
URL_ATTENDANCE_BASE = "https://app.factorialhr.com/attendance/clock-in/monthly"

# Selectores Login
SELECTOR_EMAIL = "input#user_email"
SELECTOR_PASSWORD = "input#user_password"
SELECTOR_SUBMIT = "input[name=\"commit\"]"
SELECTOR_2FA_INPUT = "input#user_code"

# Selectores Time-off (Vacaciones)
SELECTOR_TIMEOFF_MONTH_CONTAINER = "li.htyto2"
SELECTOR_TIMEOFF_MONTH_NAME = "div.htyto3"
SELECTOR_TIMEOFF_DAY_CELL = "div[role=\"button\"]"
SELECTOR_TIMEOFF_MODAL_BODY = "div._19gth1z7h"
COLOR_VACACIONES = "rgb(7, 162, 173)"
COLOR_BAJA = "rgb(255, 145, 83)"
COLOR_OTRO = "rgb(226, 226, 229)"

# Selectores Attendance (Fichaje)
SELECTOR_ATTENDANCE_ROW = "tr"
SELECTOR_POPOVER_FESTIVO = ".factorial-popover"
SELECTOR_MODAL_CONTENT_WRAPPER = "div[data-radix-popper-content-wrapper]"
SELECTOR_MODAL_BUTTON_TRABAJO = "//button[contains(text(), 'Trabajo')]" # Using XPath for text match if needed or we can iterate
SELECTOR_MODAL_INPUT_TIME = "input[placeholder=\"--:--\"]"
SELECTOR_MODAL_BUTTON_APLICAR = "//button[contains(text(), 'Aplicar')]"
SELECTOR_ROW_BUTTON_ADD = "button svg use[href*='add']"

# File paths
AUTH_FILE_PATH = "data/auth.json"
