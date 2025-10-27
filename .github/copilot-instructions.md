
<!--
Purpose: concise guidance for AI coding agents working on this repo. Keep this file short (20-50 lines), concrete, and code-linked.
-->

# Copilot / Agent Hints — PF Automation (concise)

This repo automates Practice Fusion UI tasks using Selenium + Edge. Focus on three areas: browser/session management, login flow, and post-login navigation & extraction.

- Big picture:
    - Entry: `src/main.py` (CLI). Loads `config/settings.ini`, builds an `Edge` driver via `src/automation/browser.py`, then runs `LoginAutomation` and `navigate_after_login`.
    - After navigation the code collects patient links and downloads PDFs into `Processing/<timestamp>/staging` and runs `automation.extraction.run_intake_extractor`.

- Key files to read and modify (examples):
    - `src/automation/browser.py` — Edge profile handling (uses real profile by default; headless uses a temp profile).
    - `src/automation/login.py` — Login selectors, iframe and cookie handling, post-login checks; writes debug artifacts to `.artifacts/` on failures.
    - `src/automation/navigation.py` — Clicks `id=ember43` (Schedule), ensures filter toggle, shifts date by clicking adjacent small day buttons, collects patient links and downloads intake PDFs.
    - `src/automation/ui_selectors.py` — Centralized UI CSS selectors used by generic population helpers.
    - `config/settings.ini` — Canonical place for URL, selectors and run/browser overrides (used by `main.py`).

- Project-specific patterns and conventions (do not invent):
    - Selectors come from `config/settings.ini` (login) or `ui_selectors.py` (patient UI). Selector entries use `type` (css/xpath/id/name) + `value`.
    - Edge real profile: non-headless runs pass `--user-data-dir=%LOCALAPPDATA%\Microsoft\Edge\User Data` and `--profile-directory=Default`. Headless creates a temp profile.
    - Date shifting: `select_relative_date_in_datepicker` clicks two small buttons adjacent to `#date-picker-button` — target these adjacent buttons, not global `.btn-sm` elements.
    - Downloads: intake PDFs appear in the user's Downloads folder; code moves intake*.pdf into `Processing/.../staging` and then calls the external extractor (path configurable inside `extraction.py`).

- Dev workflows & commands (PowerShell examples):
    - Create venv and install deps:

        ```powershell
        python -m venv .venv
        . .venv\Scripts\Activate.ps1
        pip install -r requirements.txt
        ```

    - Run (example):

        ```powershell
        python .\src\main.py --username "USER" --password "PASS" --config .\config\settings.ini --keep-open
        ```

- Integration points and gotchas:
    - External extractor: `automation/extraction.py` imports an external repo via sys.path (default path is hard-coded). Update `run_intake_extractor` if the extractor location differs.
    - msedgedriver: `config/settings.ini` can set `driver_path` to avoid Selenium Manager downloads; otherwise Selenium Manager fetches a driver.
    - 2FA and profile locks: real profile may prompt 2FA; when testing prefer UI (non-headless) with the Default profile. To unlock profile automatically the CLI offers `--kill-edge` which runs `taskkill` on Windows.

- When editing code:
    - Preserve the config-driven selector approach. Add new selectors to `ui_selectors.py` and prefer re-use by the generic populators in `navigation.py`.
    - Keep debug artifact writes (`.artifacts/` and `Processing/.../staging`) unchanged unless intentionally changing run outputs.

If any part of the runtime (extractor path, downloads location, Edge profile) is unclear, tell me which piece you want me to inspect or change and I will update this file accordingly.

