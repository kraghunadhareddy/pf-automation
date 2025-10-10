from __future__ import annotations

import argparse
import configparser
import sys
from pathlib import Path
from datetime import datetime

import os
import time
from automation.browser import build_edge_driver, quit_driver, EdgeConfig
from automation.login import LoginAutomation, LoginSelectors, Selector
from automation.navigation import navigate_after_login




def load_config(config_path: Path) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    if not config_path.exists():
        raise SystemExit(f"Config file not found: {config_path}")
    cfg.read(config_path, encoding="utf-8")
    return cfg


def selectors_from_config(cfg: configparser.ConfigParser) -> LoginSelectors:
    s = cfg["selectors"]
    def sel(prefix: str) -> Selector:
        return Selector(type=s.get(f"{prefix}.type"), value=s.get(f"{prefix}.value"))

    post = None
    if s.get("post_login_check.type", fallback=None) and s.get("post_login_check.value", fallback=None):
        post = sel("post_login_check")

    iframe_sel = None
    if s.get("login_iframe.type", fallback=None) and s.get("login_iframe.value", fallback=None):
        iframe_sel = sel("login_iframe")

    cookie_sel = None
    if s.get("cookie_accept.type", fallback=None) and s.get("cookie_accept.value", fallback=None):
        cookie_sel = sel("cookie_accept")

    return LoginSelectors(
        username=sel("username"),
        password=sel("password"),
        submit=sel("submit"),
        post_login_check=post,
        login_iframe=iframe_sel,
        cookie_accept=cookie_sel,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Automate login using Edge with default profile.")
    parser.add_argument("--username", required=True, help="Login username")
    parser.add_argument("--password", required=True, help="Login password")
    parser.add_argument("--config", default="config/settings.ini", help="Path to INI config file")
    parser.add_argument("--headless", action="store_true", help="Run Edge in headless mode")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--keep-open", action="store_true", help="Keep the browser open at the end for inspection")
    parser.add_argument(
        "--force-real-profile",
        action="store_true",
        help="Force using the real Default Edge profile and disable temporary profile fallback",
    )
    parser.add_argument(
        "--kill-edge",
        action="store_true",
        help="Before launching, kill any running msedge.exe processes to unlock the Default profile (Windows only)",
    )
    parser.add_argument(
        "--user-data-dir",
        help="Override Edge user-data-dir (e.g., %LOCALAPPDATA%/Microsoft/Edge/User Data)",
    )
    parser.add_argument(
        "--profile-dir",
        help="Edge profile directory name (e.g., Default, Profile 1, Profile 2)",
    )

    args = parser.parse_args(argv)

    cfg = load_config(Path(args.config))

    cfg = load_config(Path(args.config))
    base_url = cfg["site"].get("url")
    post_url = cfg["site"].get("post_login_url", fallback=None)
    # Optional run settings
    post_actions_wait = 0
    date_offset_days = -1
    if cfg.has_section("run"):
        try:
            post_actions_wait = cfg["run"].getint("wait_after_actions_seconds", fallback=0)
        except Exception:
            post_actions_wait = 0
        try:
            date_offset_days = cfg["run"].getint("date_offset_days", fallback=-1)
        except Exception:
            date_offset_days = -1

    if not base_url:
        raise SystemExit("Missing 'url' in [site] section of config.")

    selectors = selectors_from_config(cfg)

    # Optional driver/path and profile settings from [browser] section or env var
    driver_path = None
    user_data_dir = None
    profile_dir = None
    if cfg.has_section("browser"):
        driver_path = cfg["browser"].get("driver_path", fallback=None)
        user_data_dir = cfg["browser"].get("user_data_dir", fallback=None)
        profile_dir = cfg["browser"].get("profile_directory", fallback=None)
    driver_path = driver_path or os.environ.get("MSEDGEDRIVER_PATH")

    # CLI overrides
    if args.user_data_dir:
        user_data_dir = args.user_data_dir
    if args.profile_dir:
        profile_dir = args.profile_dir

    # If forcing real profile while headless, switch to UI to avoid known instability
    if args.force_real_profile and args.headless:
        print("--force-real-profile specified with --headless; switching to UI mode to use the real profile.")
        args.headless = False

    if args.kill_edge and os.name == "nt":
        import subprocess
        try:
            subprocess.run(
                ["taskkill", "/IM", "msedge.exe", "/F"],
                check=False,
                capture_output=True,
                text=True,
            )
            print("Killed running Edge processes (if any) to unlock the profile.")
        except Exception:
            print("Failed to run taskkill; continuing.")

    edge_cfg = EdgeConfig(
        headless=args.headless,
        driver_path=driver_path,
        # Disable fallback to temp UI profile when forcing real profile
        disable_fallback=bool(args.force_real_profile),
        user_data_dir=user_data_dir,
        profile_directory=profile_dir or "Default",
        suppress_browser_logs=not args.verbose,
    )
    driver = build_edge_driver(edge_cfg)

    try:
        LoginAutomation(driver, base_url, selectors).login(args.username, args.password)

        # Prepare Processing/<timestamp>/staging and processed, anchored at repo root
        script_dir = Path(__file__).resolve().parent
        repo_root = script_dir.parent
        processing_root = repo_root / "Processing"
        ts = datetime.now().strftime("%Y%m%d-%H%M")
        run_dir = processing_root / ts
        staging_dir = run_dir / "staging"
        processed_dir = run_dir / "processed"
        try:
            staging_dir.mkdir(parents=True, exist_ok=True)
            processed_dir.mkdir(parents=True, exist_ok=True)
            print(f"Processing run directory: {run_dir}")
        except Exception:
            print(f"Unable to create Processing directories at {run_dir}")

        navigate_after_login(driver, post_url, date_offset_days=date_offset_days, staging_dir=staging_dir)
        if post_actions_wait and post_actions_wait > 0:
            print(f"Waiting {post_actions_wait} seconds after navigation for verification...")
            time.sleep(post_actions_wait)
    except Exception as exc:
        print(f"Automation failed: {exc}")
        if not args.keep_open:
            quit_driver(driver)
        return 1
    if args.keep_open:
        print("--keep-open specified; leaving the browser running.")
    else:
        quit_driver(driver)

    return 0


if __name__ == "__main__":
    sys.exit(main())
