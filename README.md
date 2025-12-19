# Fucktorial Bot

This is an automated bot that intelligently fills in your timesheet on FactorialHR (https://factorialhr.com), designed to automate the repetitive task of manual clock-ins.

Powered by Python and Playwright, the script runs in a Docker container and is ideal for scheduling as a periodic cron job.

### Core Features:

*   **Secure Authentication:** Handles interactive email/password and 2FA login on the first run, then uses the saved session state for secure, non-interactive logins on subsequent runs.
*   **Intelligent Absence Detection:** Automatically scans the time-off calendar to identify vacations, sick leave, public holidays, and other custom absences. It correctly interprets full-day and half-day leave to adjust clock-in times accordingly.
*   **Automated Timesheet Filling:** Fills out the timesheet for the last 30 days based on a standard work schedule. It is smart enough to skip weekends, holidays, and any days that already have hours logged.
*   **Safe Dry-Run Mode:** By default, the bot runs in a "dry run" mode that simulates all actions without actually saving any data, allowing you to safely verify its behavior before execution.

## Prerequisites

- Docker
- Docker Compose

## Setup

1.  **Build the Docker image:**
    ```bash
    docker compose build
    ```

2.  **Initial Login:**
    The first time you run the bot, you need to perform an interactive login to provide your credentials and a 2FA code. This will create an `auth.json` file in the `data` directory to be used for subsequent runs.
    ```bash
    docker compose run --rm bot
    ```
    Follow the prompts in the console to enter your email, password, and 2FA code.

## Usage

### Dry Run

By default, the bot runs in "dry-run" mode, which simulates the entire process without actually saving any changes (it doesn't click the "Apply" button).

```bash
docker compose run --rm bot
```

### Execute Clock-in

To perform the actual clock-in and save the changes, use the `--execute` flag.

```bash
docker compose run --rm bot python src/main.py --execute
```

This command will fill in the timesheet for the 30 days prior to the execution date. You can run it periodically to catch up on any missed entries.

### Force New Login

If your session expires or you need to re-authenticate for any reason, use the `--force-login` flag. This will trigger the interactive login process again.

```bash
docker compose run --rm bot python src/main.py --force-login
```

## Testing

The project includes a test suite to verify its functionality.

### Running the Tests

To execute the test suite, run the following command:

```bash
docker compose run --rm bot pytest
```

### Test Coverage

This project uses `pytest-cov` to measure test coverage. To run the tests and generate a coverage report, use the `--cov` flag. This shows how much of the application code in the `src` directory is exercised by the tests.

```bash
docker compose run --rm bot pytest --cov=src
```
