from __future__ import annotations

import logging
from typing import Optional
import time

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

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


def ensure_filter_button_checked(driver: WebDriver, timeout: int = 20) -> None:
    """Ensure the Filter toggle (data-element="btn-filter-options") has aria-checked="true".

    If not checked, click it (with JS fallback) and wait briefly for the state to update.
    """
    wait = WebDriverWait(driver, timeout)
    try:
        btn = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-element='btn-filter-options']"))
        )
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        except Exception:
            pass

        def is_checked() -> bool:
            try:
                return (btn.get_attribute("aria-checked") or "").lower() == "true"
            except Exception:
                return False

        # Capture before-state
        before_aria = (btn.get_attribute("aria-checked") or "").lower()
        before_cls = btn.get_attribute("class") or ""

        if before_aria == "true":
            LOGGER.info("Filter | before aria-checked=%s class=%s | action=none | after aria-checked=%s class=%s",
                        before_aria, before_cls, before_aria, before_cls)
            return

        # Try to click to enable
        action = "none"
        try:
            clickable = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-element='btn-filter-options']"))
            )
            try:
                clickable.click()
                action = "click"
            except Exception:
                driver.execute_script("arguments[0].click();", clickable)
                action = "js-click"
        except Exception:
            # Fall back to JS click on the located element
            try:
                driver.execute_script("arguments[0].click();", btn)
                action = "js-click"
            except Exception:
                LOGGER.warning("Unable to click Filter button to set checked state.")
                after_aria = (btn.get_attribute("aria-checked") or "").lower()
                after_cls = btn.get_attribute("class") or ""
                LOGGER.info("Filter | before aria-checked=%s class=%s | action=failed | after aria-checked=%s class=%s",
                            before_aria, before_cls, after_aria, after_cls)
                return

        # Wait briefly for aria-checked to become true
        try:
            WebDriverWait(driver, 8).until(
                lambda d: (d.find_element(By.CSS_SELECTOR, "[data-element='btn-filter-options']")
                           .get_attribute("aria-checked") or "").lower() == "true"
            )
            # Capture after-state and log summary
            fresh = driver.find_element(By.CSS_SELECTOR, "[data-element='btn-filter-options']")
            after_aria = (fresh.get_attribute("aria-checked") or "").lower()
            after_cls = fresh.get_attribute("class") or ""
            LOGGER.info("Filter | before aria-checked=%s class=%s | action=%s | after aria-checked=%s class=%s",
                        before_aria, before_cls, action, after_aria, after_cls)
        except Exception:
            # Log what we could observe
            try:
                fresh = driver.find_element(By.CSS_SELECTOR, "[data-element='btn-filter-options']")
                after_aria = (fresh.get_attribute("aria-checked") or "").lower()
                after_cls = fresh.get_attribute("class") or ""
            except Exception:
                after_aria, after_cls = "", ""
            LOGGER.warning("Filter | before aria-checked=%s class=%s | action=%s | after aria-checked=%s class=%s | note=did-not-confirm-checked",
                           before_aria, before_cls, action, after_aria, after_cls)
    except TimeoutException:
        LOGGER.info("Filter button [data-element='btn-filter-options'] not found; skipping.")
    except Exception:
        LOGGER.debug("Error while ensuring Filter button checked.", exc_info=True)


def select_relative_date_in_datepicker(driver: WebDriver, offset_days: int = -1, timeout: int = 30) -> None:
    """Shift the date by clicking the two day-nav buttons adjacent to the date picker.

    offset_days: 0=today, -1=yesterday, 1=tomorrow, etc.
    Ensures we target the buttons right next to the date picker to avoid other .btn-sm on the page.
    """
    if offset_days == 0:
        LOGGER.info("Date shift offset is 0; no action needed.")
        return

    wait = WebDriverWait(driver, timeout)

    # Ensure page is idle before interacting
    try:
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

    try:
        date_btn = wait.until(EC.presence_of_element_located((By.ID, "date-picker-button")))
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", date_btn)
        except Exception:
            pass

        def resolve_adjacent_buttons() -> tuple[Optional[WebElement], Optional[WebElement]]:
            """Get strictly-adjacent prev/next sibling buttons to the date picker button.

            Prev: preceding-sibling button with classes (btn-sm, border--LRn, rotate-180)
            Next: following-sibling button with class (btn-sm) and NOT the prev-specific classes.
            """
            prev_b = None
            next_b = None
            # 0) Prefer container-scoped descendant search within flex-row (handles nested wrappers)
            try:
                flex_row = date_btn.find_element(
                    By.XPATH,
                    "ancestor::div[contains(@class,'item--TBn') and contains(@class,'box-fixed')]//div[contains(@class,'flex-row')][.//button[@id='date-picker-button']][1]",
                )
                # Prev: prefer the first following candidate after the date button; else the closest preceding one
                try:
                    prev_b = flex_row.find_element(
                        By.XPATH,
                        "(.//button[contains(@class,'btn-sm') and contains(@class,'border--LRn') and contains(@class,'rotate-180')][preceding::button[@id='date-picker-button']])[1]",
                    )
                except Exception:
                    try:
                        prev_b = flex_row.find_element(
                            By.XPATH,
                            "(.//button[contains(@class,'btn-sm') and contains(@class,'border--LRn') and contains(@class,'rotate-180')][following::button[@id='date-picker-button']])[last()]",
                        )
                    except Exception:
                        prev_b = None
                # Next: prefer the first following candidate after the date button; else the closest preceding one
                try:
                    next_b = flex_row.find_element(
                        By.XPATH,
                        "(.//button[contains(@class,'btn-sm') and not(contains(@class,'border--LRn')) and not(contains(@class,'rotate-180'))][preceding::button[@id='date-picker-button']])[1]",
                    )
                except Exception:
                    try:
                        next_b = flex_row.find_element(
                            By.XPATH,
                            "(.//button[contains(@class,'btn-sm') and not(contains(@class,'border--LRn')) and not(contains(@class,'rotate-180'))][following::button[@id='date-picker-button']])[last()]",
                        )
                    except Exception:
                        next_b = None
                if prev_b and next_b:
                    return prev_b, next_b
            except Exception:
                pass
            # 1) Prefer strict adjacency via sibling axis
            try:
                prev_b = date_btn.find_element(
                    By.XPATH,
                    "preceding-sibling::button[contains(@class,'btn-sm') and contains(@class,'border--LRn') and contains(@class,'rotate-180')][1]",
                )
            except Exception:
                prev_b = None
            try:
                next_b = date_btn.find_element(
                    By.XPATH,
                    "following-sibling::button[contains(@class,'btn-sm') and not(contains(@class,'border--LRn')) and not(contains(@class,'rotate-180'))][1]",
                )
            except Exception:
                next_b = None
            if prev_b and next_b:
                return prev_b, next_b
            # 2) As a conservative fallback, inspect immediate parent only and pick neighbors around the date_btn
            try:
                parent = date_btn.find_element(By.XPATH, "..")
                children = parent.find_elements(By.XPATH, "./*")
                # Find index of date_btn among children
                idx = None
                for i, c in enumerate(children):
                    try:
                        if c.id == date_btn.id:
                            idx = i
                            break
                    except Exception:
                        continue
                if idx is not None:
                    # Helper classifiers
                    def is_prev_btn(el) -> bool:
                        try:
                            cls = (el.get_attribute("class") or "")
                            return ("btn-sm" in cls) and ("border--LRn" in cls) and ("rotate-180" in cls)
                        except Exception:
                            return False

                    def is_next_btn(el) -> bool:
                        try:
                            cls = (el.get_attribute("class") or "")
                            return ("btn-sm" in cls) and ("border--LRn" not in cls) and ("rotate-180" not in cls)
                        except Exception:
                            return False

                    # Nearest-neighbor scan: find the closest matching buttons in either direction
                    n = len(children)
                    if not prev_b:
                        try:
                            for d in range(1, n):
                                r = idx + d
                                if r < n and is_prev_btn(children[r]):
                                    prev_b = children[r]
                                    break
                                l = idx - d
                                if l >= 0 and is_prev_btn(children[l]):
                                    prev_b = children[l]
                                    break
                        except Exception:
                            pass
                    if not next_b:
                        try:
                            for d in range(1, n):
                                r = idx + d
                                if r < n and is_next_btn(children[r]):
                                    next_b = children[r]
                                    break
                                l = idx - d
                                if l >= 0 and is_next_btn(children[l]):
                                    next_b = children[l]
                                    break
                        except Exception:
                            pass
            except Exception:
                pass
            return prev_b, next_b

        # Validate we can resolve at least the required direction button
        steps = abs(offset_days)
        direction = 'next' if offset_days > 0 else 'prev'
        prev_btn, next_btn = resolve_adjacent_buttons()
        if offset_days < 0 and not prev_btn:
            LOGGER.warning("Previous-day button not found strictly adjacent to date picker; cannot shift %s days back.", abs(offset_days))
            return
        if offset_days > 0 and not next_btn:
            LOGGER.warning("Next-day button not found strictly adjacent to date picker; cannot shift %s days forward.", abs(offset_days))
            return

        LOGGER.info("Date shift | offset=%s | steps=%s | method=adjacent-%s-button", offset_days, steps, direction)
        last_err = None
        for i in range(steps):
            try:
                # Re-resolve each iteration to avoid stale references after UI refresh
                prev_btn, next_btn = resolve_adjacent_buttons()
                target = next_btn if offset_days > 0 else prev_btn
                if not target:
                    LOGGER.warning("Step %s/%s: %s-day button not found; stopping.", i + 1, steps, direction)
                    break
                # Wait until clickable
                # Scroll target into view, then attempt click
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", target)
                except Exception:
                    pass
                try:
                    target.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", target)
                _wait_for_data_load(driver, timeout=15)
                time.sleep(0.1)
            except StaleElementReferenceException as se:
                last_err = se
                time.sleep(0.1)
                continue
            except Exception as e:
                last_err = e
                LOGGER.debug("Step %s/%s: error clicking %s-day button", i + 1, steps, direction, exc_info=True)
                time.sleep(0.2)
        if last_err:
            LOGGER.debug("Date shift completed with last error: %s", repr(last_err))
        LOGGER.info("Date shift complete | offset=%s | attempted steps=%s", offset_days, steps)
    except TimeoutException:
        LOGGER.warning("Date picker button (id=date-picker-button) not present within %ss; skipping date shift.", timeout)
    except Exception:
        LOGGER.debug("Error while shifting date by offset.", exc_info=True)


def print_patient_links_from_table(driver: WebDriver, timeout: int = 15) -> list[str]:
    """Collect links that match required pattern after date change and return them.

    Criteria:
    - Anchor elements must be within table.data-table__grid
    - href must contain "/PF/charts/patients/"
    - route must end with "summary" (supports SPA hash routes; ignores query and trailing slash)

    Returns: a list of matching href strings (may be empty on no matches or failure)
    """
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.data-table__grid"))
        )
    except TimeoutException:
        LOGGER.info("table.data-table__grid not found within %ss; skipping patient link collection.", timeout)
        return []
    except Exception:
        LOGGER.debug("Error locating table.data-table__grid.", exc_info=True)
        return []

    try:
        anchors = driver.find_elements(By.CSS_SELECTOR, "table.data-table__grid a[href*='/PF/charts/patients/']")
        from urllib.parse import urlparse, unquote
        links: list[str] = []
        for a in anchors:
            try:
                href = a.get_attribute("href") or ""
                if "/PF/charts/patients/" not in href:
                    continue
                # Handle SPA URLs where the app routes live in the fragment after '#'
                parsed = urlparse(href)
                path = unquote(parsed.path or "")
                frag = unquote(parsed.fragment or "")

                def ends_with_summary(s: str) -> bool:
                    s = s.split("?")[0].rstrip("/")
                    return s.endswith("summary")

                # Prefer inspecting fragment if it contains the PF route; else fall back to path
                contains_in_frag = "/PF/charts/patients/" in frag
                contains_in_path = "/PF/charts/patients/" in path
                if not (contains_in_frag or contains_in_path):
                    continue

                candidate = frag if contains_in_frag else path
                if ends_with_summary(candidate):
                    links.append(href)
            except Exception:
                continue
        # De-duplicate while preserving order
        seen = set()
        ordered_unique = []
        for href in links:
            if href not in seen:
                seen.add(href)
                ordered_unique.append(href)
        if not ordered_unique:
            LOGGER.info("No matching patient links (ending with 'summary') found under table.data-table__grid.")
        return ordered_unique
    except Exception:
        LOGGER.debug("Error while extracting patient links.", exc_info=True)
        return []


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

    # After Schedule loads, ensure the Filter toggle is checked
    ensure_filter_button_checked(driver)

    # After Schedule loads, shift the date using the adjacent prev/next buttons
    select_relative_date_in_datepicker(driver, offset_days=date_offset_days)

    # After date change, collect patient chart links and print them
    links = print_patient_links_from_table(driver)
    if links:
        print("\n".join(links))
        LOGGER.info("Collected %s patient links; beginning per-link navigation.", len(links))
    else:
        LOGGER.info("No patient links collected; skipping per-link navigation.")

    # Loop through the collected links, opening each in the same browser window and pausing 5 seconds
    for idx, href in enumerate(links, start=1):
        try:
            LOGGER.info("[%s/%s] Opening patient link: %s", idx, len(links), href)
            driver.get(href)
            time.sleep(5)
        except Exception:
            LOGGER.debug("Error opening patient link: %s", href, exc_info=True)

    if not url:
        LOGGER.info("No post-login URL provided; staying on current page.")
        return
    LOGGER.info("Navigating to %s", url)
    driver.get(url)
