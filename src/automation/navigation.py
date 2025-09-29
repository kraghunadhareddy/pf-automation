from __future__ import annotations

import logging
from typing import Optional
from datetime import datetime, timedelta
import time

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

LOGGER = logging.getLogger(__name__)


def click_schedule(driver: WebDriver, timeout: int = 30) -> None:
    """Click the Schedule item after login (element id='ember43')."""
    def _wait_for_idle(max_wait: int = timeout) -> None:
        wait_idle = WebDriverWait(driver, max_wait)
        # Common overlay/spinner selectors to wait to disappear
        overlay_selectors = [
            ".spinner-overlay.is-active",
            ".spinner-overlay",
            ".loading",
            ".busy",
            ".pf-spinner",
        ]
        for sel in overlay_selectors:
            try:
                wait_idle.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, sel)))
            except Exception:
                # If selector not found or already invisible, continue
                pass

    try:
        driver.switch_to.default_content()
    except Exception:
        pass

    wait = WebDriverWait(driver, timeout)
    try:
        el = wait.until(EC.element_to_be_clickable((By.ID, "ember43")))
        el.click()
        LOGGER.info("Clicked on 'Schedule' (id=ember43).")
        # Wait for potential loading spinner after navigation
        _wait_for_idle()
    except TimeoutException:
        LOGGER.warning("'Schedule' (id=ember43) not found/clickable within %ss; skipping.", timeout)
    except Exception:
        LOGGER.warning("Failed to click 'Schedule' (id=ember43).", exc_info=True)


def _format_aria_label_for_date(d: datetime) -> list[str]:
    # Common aria-label formats: "September 28, 2025" or without comma
    month = d.strftime("%B")
    day = str(d.day)
    year = str(d.year)
    return [f"{month} {day}, {year}", f"{month} {day} {year}"]


def select_relative_date_in_datepicker(driver: WebDriver, offset_days: int = -1, timeout: int = 30) -> None:
    """Open the date picker and select date relative to today using offset_days.

    offset_days: 0=today, -1=yesterday, 1=tomorrow, etc.
    Tries strategies: data-date, aria-labels, then day-text fallback.
    """
    wait = WebDriverWait(driver, timeout)

    # Ensure page is idle before interacting
    try:
        # Reuse idle wait from above by checking common overlays
        for sel in [
            ".spinner-overlay.is-active",
            ".spinner-overlay",
            ".loading",
            ".busy",
            ".pf-spinner",
        ]:
            try:
                WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, sel)))
            except Exception:
                pass
    except Exception:
        pass

    # Ensure we're on the Schedule view by waiting for the date button
    try:
        btn = wait.until(EC.element_to_be_clickable((By.ID, "date-picker-button")))
        # Scroll into view and attempt safe click with fallback
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", btn)
        except Exception:
            pass
        try:
            btn.click()
        except Exception:
            # Wait a bit and JS-click as fallback to avoid overlays
            try:
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "date-picker-button")))
            except Exception:
                pass
            driver.execute_script("arguments[0].click();", btn)
        LOGGER.info("Opened date picker (id=date-picker-button).")
    except TimeoutException:
        LOGGER.warning("Date picker button (id=date-picker-button) not clickable within %ss; skipping.", timeout)
        return
    except Exception:
        LOGGER.warning("Failed to open date picker (id=date-picker-button).", exc_info=True)
        return

    target = datetime.now() + timedelta(days=offset_days)
    iso = target.strftime("%Y-%m-%d")
    aria_labels = _format_aria_label_for_date(target)

    # Wait briefly for the date grid to render
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-date], button[aria-label]"))
        )
    except Exception:
        pass

    # Try quick direct matches with small polling and JS-click
    selectors = [
        f"[data-date='{iso}']",
        f"button[aria-label='{aria_labels[0]}']",
        f"*[aria-label='{aria_labels[0]}']",
        f"button[aria-label='{aria_labels[1]}']",
        f"*[aria-label='{aria_labels[1]}']",
    ]

    # Try for a short window; attempt both attribute-based and day-text fallback each iteration
    end_time = time.time() + min(timeout, 6)
    day_text = str(target.day)
    while time.time() < end_time:
        for sel in selectors:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
            except Exception:
                el = None
            if el and el.is_displayed():
                try:
                    driver.execute_script("arguments[0].click();", el)
                    LOGGER.info("Selected date (offset %s) via selector: %s", offset_days, sel)
                    # After selection, wait for data load
                    _wait_for_data_load(driver)
                    return
                except Exception:
                    LOGGER.debug("JS click failed for selector %s", sel, exc_info=True)
        # Try day-text fallback in the same loop for speed
        try:
            candidates = driver.find_elements(By.XPATH, f"//*[self::button or self::td or self::div][normalize-space(text())='{day_text}']")
            for c in candidates:
                try:
                    if c.is_displayed() and c.is_enabled():
                        driver.execute_script("arguments[0].click();", c)
                        LOGGER.info("Selected date (offset %s) by day text fallback: %s", offset_days, day_text)
                        _wait_for_data_load(driver)
                        return
                except Exception:
                    continue
        except Exception:
            pass
        time.sleep(0.3)

    LOGGER.warning("Failed to select date for offset %s; refine selectors or increase timeout.", offset_days)


def _wait_for_data_load(driver: WebDriver, timeout: int = 30) -> None:
    """Wait for common spinners/overlays to disappear after date selection."""
    wait_idle = WebDriverWait(driver, timeout)
    overlay_selectors = [
        ".spinner-overlay.is-active",
        ".spinner-overlay",
        ".loading",
        ".busy",
        ".pf-spinner",
    ]
    for sel in overlay_selectors:
        try:
            wait_idle.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, sel)))
        except Exception:
            pass


def navigate_after_login(driver: WebDriver, url: Optional[str] = None, date_offset_days: int = -1) -> None:
    # Always attempt to click the 'Schedule' item once we believe we're logged in
    click_schedule(driver)

    # After Schedule loads, open the date picker and select yesterday
    select_relative_date_in_datepicker(driver, offset_days=date_offset_days)

    if not url:
        LOGGER.info("No post-login URL provided; staying on current page.")
        return
    LOGGER.info("Navigating to %s", url)
    driver.get(url)
