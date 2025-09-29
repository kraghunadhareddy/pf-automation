# PF Automation

Automate login to a website using Microsoft Edge (Chromium) with your existing Edge profile, so site trust and cookies persist.

## Features
- Edge with your real Windows Edge profile (cookies/trust preserved)
- Credentials via command line (no secrets in files)
- Site URL and selectors in `config/settings.ini`
- Selenium 4 with smart waits
 - Optional headless mode (uses a temp profile)
 - Debug artifacts (screenshots/HTML) saved to `.artifacts` on timeouts
 - Post-login navigation: clicks "Schedule", ensures "Filter" is active, and shifts the date by using the two day-step buttons next to the date picker

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

## Notes on Edge Profile and 2FA
- Real profile: by default we use `%LOCALAPPDATA%\Microsoft\Edge\User Data` and `Default` profile; you can set a different profile with `--profile-dir` or in `[browser]` of `config/settings.ini`.
- 2FA: If the site prompts for 2FA when headless or on a new profile, switch to visible UI with your real profile (or pass `--user-data-dir` and `--profile-dir`) to avoid repeated 2FA.

## Project Structure
- `src/automation/browser.py` — builds Edge driver using default profile
- `src/automation/login.py` — logs into the site using config selectors
- `src/automation/navigation.py` — sample post-login navigation
- `src/main.py` — CLI entrypoint
- `config/settings.ini` — site URL and selectors

## Troubleshooting
- WebDriver errors: ensure Edge and msedgedriver match; a local driver can be set in `[browser] driver_path`.
- Element not found: update selectors in `config/settings.ini` to match your site.
- Profile lock: close running Edge windows or run with `--kill-edge` to unlock.
 - Date not changing: the automation clicks the left/right small day-step buttons that sit right next to the date picker button. If your UI changed, verify those two buttons are adjacent to `#date-picker-button` and keep their classes (prev has `btn-sm border--LRn rotate-180`).

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
