from __future__ import annotations

import logging
import os
import sys
import tempfile
import shutil
from dataclasses import dataclass
from typing import Optional

from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
try:
    from selenium.webdriver.edge.service import Service as EdgeService  # type: ignore
except Exception:  # pragma: no cover
    EdgeService = None  # type: ignore


LOGGER = logging.getLogger(__name__)


@dataclass
class EdgeConfig:
    headless: bool = False
    user_data_dir: Optional[str] = None
    profile_directory: str = "Default"
    driver_path: Optional[str] = None
    cleanup_user_data_dir: bool = False
    disable_fallback: bool = False
    suppress_browser_logs: bool = True


def get_default_edge_user_data_dir() -> str:
    """Return the default Edge user data directory on Windows.

    Typically %LOCALAPPDATA%\\Microsoft\\Edge\\User Data
    """
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError("LOCALAPPDATA environment variable not set. Are you on Windows?")
    return os.path.join(local_app_data, "Microsoft", "Edge", "User Data")


def build_edge_driver(config: Optional[EdgeConfig] = None) -> webdriver.Edge:
    """Create and return a Selenium Edge WebDriver configured to use the default profile.

    Uses Selenium Manager to resolve the driver automatically.
    """
    config = config or EdgeConfig()
    options = EdgeOptions()
    # Reduce noisy Chromium stderr logs unless explicitly disabled
    if config.suppress_browser_logs:
        try:
            options.add_experimental_option("excludeSwitches", ["enable-logging"])  # type: ignore
        except Exception:
            pass
        options.add_argument("--log-level=3")

    # Determine user-data-dir/profile
    default_user_data_dir = config.user_data_dir or get_default_edge_user_data_dir()

    temp_user_data_dir: Optional[str] = None
    if config.headless:
        # Headless + existing real profile often crashes on Windows.
        # Use a temporary clean profile for headless stability.
        temp_user_data_dir = tempfile.mkdtemp(prefix="edge-profile-")
        options.add_argument(f"--user-data-dir={temp_user_data_dir}")
        options.add_argument(f"--profile-directory=Default")
        # New Edge headless mode
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
    else:
        # Use provided user-data-dir or the real default profile when not headless
        options.add_argument(f"--user-data-dir={default_user_data_dir}")
        options.add_argument(f"--profile-directory={config.profile_directory}")

    # Stability options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Disabling extensions can crash when loading a real user profile; keep extensions enabled in UI mode
    if config.headless:
        options.add_argument("--disable-extensions")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--remote-debugging-port=0")

    LOGGER.debug("Launching Edge with user-data-dir=%s, profile=%s, headless=%s",
                 temp_user_data_dir or default_user_data_dir, config.profile_directory, config.headless)

    # If a driver_path is provided (via config or env), use it to avoid network fetches
    service = None
    if config.driver_path:
        LOGGER.debug("Using provided msedgedriver path: %s", config.driver_path)
        if EdgeService:
            service = EdgeService(executable_path=config.driver_path)  # type: ignore
        else:
            # Fallback: prepend driver directory to PATH so webdriver.Edge can find it
            driver_dir = os.path.dirname(config.driver_path)
            os.environ["PATH"] = driver_dir + os.pathsep + os.environ.get("PATH", "")
            LOGGER.debug("Prepended driver dir to PATH: %s", driver_dir)

    try:
        driver = webdriver.Edge(options=options, service=service)
    except Exception as exc:
        LOGGER.error("Failed to start Edge WebDriver: %s", exc)
        raise

    driver.set_window_size(1366, 900)

    # Attach temp profile path for cleanup on quit
    if temp_user_data_dir:
        setattr(driver, "_temp_user_data_dir", temp_user_data_dir)
    elif config.user_data_dir and config.cleanup_user_data_dir:
        # Mark provided user-data-dir for cleanup on quit when requested
        setattr(driver, "_temp_user_data_dir", config.user_data_dir)
    return driver


def quit_driver(driver: webdriver.Edge) -> None:
    try:
        driver.quit()
    except Exception:
        LOGGER.debug("Error during driver.quit()", exc_info=True)
    # Cleanup temporary profile if used
    temp_dir = getattr(driver, "_temp_user_data_dir", None)
    if temp_dir:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            LOGGER.debug("Removed temporary user-data-dir: %s", temp_dir)
        except Exception:
            LOGGER.debug("Failed to remove temporary user-data-dir: %s", temp_dir, exc_info=True)
