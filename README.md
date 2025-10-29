# PF Automation

Automates Practice Fusion UI workflows using Selenium + Edge with your real Edge profile (cookies/trust preserved).

## Features
- Real Edge profile (persisted cookies/trust) or headless with a temp profile
- Credentials via command line (no secrets in files)
- Config-driven selectors and run settings in `config/settings.ini`
- Selenium 4 with robust waits and defensive fallbacks
- Debug artifacts on errors (screenshots/HTML) under `artifacts/`
- Post-login navigation with multi-facility flows:
	- Schedule → Date → Facility → Appointments → Process patients
	- Facility dropdown: resilient open/list/select logic with diagnostics
	- Date shifting: uses the two small prev/next buttons adjacent to `#date-picker-button`
	- Persistent logs to `log.txt` when running with `--verbose`

## Prerequisites
- Windows 10/11
- Microsoft Edge (Chromium)
- Python 3.10+

## Setup (PowerShell)
```powershell
# 1) Create venv
python -m venv .venv

# 2) Activate
. .venv\Scripts\Activate.ps1

# 3) Install deps
pip install -r requirements.txt
```

## Configure
Edit `config/settings.ini`:
- `[site]` `url` = login page; `post_login_url` optional
- `[selectors]` provide selector type and value for username, password, submit, and optional post_login_check
- `[run]` optional `wait_after_actions_seconds` to pause at the end so you can verify the UI
	- `date_offset_days` shifts the date using the small previous/next buttons adjacent to the date picker button (0=today, -1=yesterday, 1=tomorrow)
- `[facilities]` optional list of centers to process (defaults to this list when no CLI overrides):

Example:

```ini
[facilities]
names = (Gilbert) Balance Hormone Center, (Scottsdale) Balance Hormone Center, Chandler-Balance Hormone Center
```

You can also put one per line by using newlines; commas and newlines are both supported.

Supported selector types: css, xpath, id, name

## Run
Provide username and password via args:

```powershell
python .\src\main.py --username "YOUR_USER" --password "YOUR_PASS" --config .\config\settings.ini --keep-open
```

Useful flags:
- `--keep-open` keep the browser open after the run for inspection
- `--verbose` enable detailed logs
- `--headless` run without a visible browser (uses a temporary clean profile)
- `--force-real-profile` never fallback to a temp profile; error if the real one can’t launch
- `--kill-edge` kill running msedge.exe to unlock the real profile before launch
- `--user-data-dir` and `--profile-dir` to target the exact profile you use (e.g., `Profile 1`)

### Facilities control
- Process named centers from CLI (overrides config):

```powershell
python .\src\main.py --username "YOUR_USER" --password "YOUR_PASS" --config .\config\settings.ini \
	--hormone-center "(Scottsdale) Balance Hormone Center" \
	--hormone-center "(Gilbert) Balance Hormone Center" --verbose
```

- Process all detected Hormone Centers:

```powershell
python .\src\main.py --username "YOUR_USER" --password "YOUR_PASS" --config .\config\settings.ini --all-hormone-centers --verbose
```

- Process centers from config (no CLI flags required):

```powershell
python .\src\main.py --username "YOUR_USER" --password "YOUR_PASS" --config .\config\settings.ini --verbose
```

CLI precedence:
1) `--hormone-center` (repeatable) → explicit list
2) `--all-hormone-centers` → all detected
3) `[facilities].names` in config → default list
4) Else → single-center navigation flow

## Notes on Edge Profile and 2FA
- Real profile: by default we use `%LOCALAPPDATA%\Microsoft\Edge\User Data` and `Default` profile; you can set a different profile with `--profile-dir` or in `[browser]` of `config/settings.ini`.
- 2FA: If the site prompts for 2FA when headless or on a new profile, switch to visible UI with your real profile (or pass `--user-data-dir` and `--profile-dir`) to avoid repeated 2FA.

## Project Structure
- `src/automation/browser.py` — builds Edge driver using default profile
- `src/automation/login.py` — logs into the site using config selectors
- `src/automation/navigation.py` — post-login navigation, downloads, summaries, and multi-center processing
- `src/main.py` — CLI entrypoint
- `config/settings.ini` — site URL and selectors
 - `artifacts/` — debug captures for troubleshooting
 - `Processing/<timestamp>/{staging,processed}` — per-run outputs

## Troubleshooting
- WebDriver errors: ensure Edge and msedgedriver match; a local driver can be set in `[browser] driver_path`.
- Element not found: update selectors in `config/settings.ini` to match your site.
- Profile lock: close running Edge windows or run with `--kill-edge` to unlock.
 - Date not changing: the automation clicks the left/right small day-step buttons that sit right next to the date picker button. If your UI changed, verify those two buttons are adjacent to `#date-picker-button` and keep their classes (prev has `btn-sm border--LRn rotate-180`).
 - Facility dropdown not opening or selection failing: run with `--verbose` and check `log.txt` for lines like “Facilities dropdown opened via …” and the list of available options.
 - Appointments tab: the flow ensures the “Appointments” tab is active before processing; if your environment labels differ, update `UI_SELECTORS['schedule_tabs']['appointments']`.

## VS Code Tasks
- Run automation (Headless)
- Run automation (UI)

## GitHub
Initialize and push:
```powershell
git init
git add .
git commit -m "feat: initial PF automation with Edge real profile support"
git branch -M main
git remote add origin https://github.com/<your-username>/pf-automation.git
git push -u origin main
```
