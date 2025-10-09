from selenium.webdriver.remote.webdriver import WebDriver
from pathlib import Path
def _build_nutrition_history_summary(intake_json: Path) -> str:
    """Summarize supplements from the Nutrition History section."""
    import json
    try:
        data = json.loads(intake_json.read_text(encoding="utf-8", errors="ignore") or "{}")
    except Exception:
        return ""

    pages = data.get("pages") or []
    supplements = []
    for page in pages:
        for section in page.get("sections", []) or []:
            sec_name = (section.get("section") or "").strip().lower()
            if "supplements" in sec_name or "please list all current supplements" in sec_name:
                for cb in section.get("checkboxes", []) or []:
                    label = (cb.get("label") or "").strip()
                    status = (cb.get("status") or "").lower()
                    if status == "ticked" and label:
                        supplements.append(label)
    if supplements:
        return "Supplements: " + ", ".join(supplements)
    return ""

def _populate_nutrition_history(driver, summary_text, timeout=15) -> bool:
    """Open nutrition history editor, populate textarea, and save."""
    import time
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
    import logging
    LOGGER = logging.getLogger(__name__)
    LOGGER.info(f"NutritionHistory | Attempting UI fill | summary_text: {summary_text!r}")
    if not summary_text.strip():
        LOGGER.info("Nutrition history summary is empty; skipping population.")
        return False
    wait = WebDriverWait(driver, timeout)
    _dismiss_any_popups(driver)
    add_mode_entered = False
    # Try main add button, fallback to edit button
    try:
        section_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-element='nutritionHistory-section']")))
        _dismiss_any_popups(driver)
        try:
            add_btn = section_container.find_element(By.CSS_SELECTOR, "[data-element='past-medical-history-field-add-button']")
        except Exception:
            add_btn = section_container.find_element(By.CSS_SELECTOR, "[data-element='past-medical-history-field-item-0']")
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_btn)
        except Exception:
            pass
        _dismiss_any_popups(driver)
        try:
            add_btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", add_btn)
        add_mode_entered = True
    except Exception:
        LOGGER.info("Nutrition history UI elements not found / not filled.")
        return False

    # Text area
    _dismiss_any_popups(driver)
    try:
        textarea = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-element='nutritionHistory-detail-text-area']")))
        LOGGER.info("NutritionHistory | Found textarea element, attempting to fill.")
    except Exception:
        LOGGER.info("Nutrition history textarea not found.")
        return False
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", textarea)
    except Exception:
        pass
    try:
        textarea.clear()
    except Exception:
        try:
            textarea.send_keys(Keys.CONTROL, 'a')
            textarea.send_keys(Keys.DELETE)
        except Exception:
            pass
    try:
        textarea.send_keys(summary_text)
        driver.execute_script("arguments[0].blur();", textarea)
        LOGGER.info(f"NutritionHistory | textarea value after fill: {textarea.get_attribute('value')!r}")
    except Exception as e:
        LOGGER.error(f"Failed to send nutrition history summary to textarea: {e}")
        _capture_nutrition_debug(driver, "sendkeys-fail")
        return False

    # Save button
    _dismiss_any_popups(driver)
    try:
        save_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-element='btn-save']")))
        LOGGER.info("NutritionHistory | Found save button, attempting to click.")
    except Exception as e:
        LOGGER.error(f"Nutrition history save button not found: {e}")
        _capture_nutrition_debug(driver, "no-save-btn")
        return False
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_btn)
    except Exception as e:
        LOGGER.warning(f"Nutrition history: failed to scroll save button into view: {e}")
        _capture_nutrition_debug(driver, "scroll-save-fail")
    try:
        save_btn.click()
    except Exception as e:
        LOGGER.error(f"Nutrition history: failed to click save button: {e}")
        _capture_nutrition_debug(driver, "click-save-fail")
        try:
            driver.execute_script("arguments[0].click();", save_btn)
        except Exception as e2:
            LOGGER.warning(f"Nutrition history: JS click save button failed: {e2}")
            _capture_nutrition_debug(driver, "js-click-save-fail")
            return False
    try:
        WebDriverWait(driver, 5).until(
            lambda d: (not save_btn.is_displayed()) or (not save_btn.is_enabled())
        )
    except Exception as e:
        LOGGER.warning(f"Nutrition history: save button did not disappear/disable: {e}")
        _capture_nutrition_debug(driver, "save-btn-not-disappear")
        try:
            _wait_for_data_load(driver, timeout=5)
        except Exception as e2:
            LOGGER.info(f"Nutrition history save button did not disappear or disable after click: {e2}")
            _capture_nutrition_debug(driver, "save-btn-wait-data-fail")
            return False
    LOGGER.info("Filled nutrition history text area for patient.")
    return True

def _capture_nutrition_debug(driver, reason: str):
    """Capture screenshot and page source for nutrition history debug."""
    import os, time
    ts = time.strftime("%Y%m%d-%H%M%S")
    outdir = os.path.join(os.getcwd(), "artifacts")
    os.makedirs(outdir, exist_ok=True)
    try:
        fname = f"nutrition_debug_{reason}_{ts}.png"
        driver.save_screenshot(os.path.join(outdir, fname))
    except Exception:
        pass
    try:
        fname = f"nutrition_debug_{reason}_{ts}.html"
        with open(os.path.join(outdir, fname), "w", encoding="utf-8", errors="ignore") as f:
            f.write(driver.page_source)
    except Exception:
        pass
from pathlib import Path
# ---------------- Ongoing Medical Problems Summary Helpers -----------------
def _build_ongoing_medical_problems_summary(intake_json: Path) -> str:
    """Summarize Reason for visit/Ongoing Medical Problems section: list ticked labels."""
    try:
        data = json.loads(intake_json.read_text(encoding="utf-8", errors="ignore") or "{}")
    except Exception:
        return ""

    pages = data.get("pages") or []
    ticked_labels = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        for section in page.get("sections", []) or []:
            if not isinstance(section, dict):
                continue
            sec_name = (section.get("section") or "").strip().lower()
            if sec_name == "reason for visit/ongoing medical problems":
                for cb in section.get("checkboxes", []) or []:
                    if not isinstance(cb, dict):
                        continue
                    label = (cb.get("label") or "").strip()
                    status = (cb.get("status") or "").lower()
                    if status == "ticked" and label:
                        ticked_labels.append(label)

    if ticked_labels:
        return "Ticked Problems: " + ", ".join(ticked_labels)
    return ""

def _populate_ongoing_medical_problems(driver: WebDriver, summary_text: str, timeout: int = 15) -> bool:
    # ...existing code...
    """Open the ongoing medical problems editor, populate textarea, and save."""
    if not summary_text.strip():
        return False
    wait = WebDriverWait(driver, timeout)
    # Dismiss any popups before starting
    _dismiss_any_popups(driver)
    add_mode_entered = False
    # Try main add button, fallback to edit button

# --- Major Events Summary Helper ---
def _build_major_events_summary(intake_json: Path) -> str:
    """Summarize Surgeries/Major Events section: list ticked labels and Q/A pairs."""
    try:
        data = json.loads(intake_json.read_text(encoding="utf-8", errors="ignore") or "{}")
    except Exception:
        return ""

    pages = data.get("pages") or []
    ticked_labels = []
    qa_pairs = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        for section in page.get("sections", []) or []:
            if not isinstance(section, dict):
                continue
            sec_name = (section.get("section") or "").strip().lower()
            if sec_name == "surgeries/major events":
                for cb in section.get("checkboxes", []) or []:
                    label = (cb.get("label") or "").strip()
                    if cb.get("checked") and label:
                        ticked_labels.append(label)
        for resp in page.get("responses", []) or []:
            if not isinstance(resp, dict):
                continue
            rsec = (resp.get("section") or "").strip().lower()
            if rsec == "surgeries/major events":
                for q in resp.get("questions", []) or []:
                    qtext = (q.get("question") or "").strip()
                    ans = (q.get("answer") or "").strip()
                    if qtext and ans:
                        qa_pairs.append((qtext, ans))

    lines = []
    if ticked_labels:
        lines.append("Ticked Events: " + ", ".join(ticked_labels))
    for q, a in qa_pairs:
        lines.append(f"{q}: {a}")
    return "\n".join(lines)
    # Remove misplaced code block (should not be here)

    pages = data.get("pages") or []
    ticked_labels = []
    qa_pairs = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        for section in page.get("sections", []) or []:
            if not isinstance(section, dict):
                continue
            sec_name = (section.get("section") or "").strip().lower()
            if sec_name == "surgeries/major events":
                for cb in section.get("checkboxes", []) or []:
                    if not isinstance(cb, dict):
                        continue
                    label = (cb.get("label") or "").strip()
                    status = (cb.get("status") or "").lower()
                    if status == "ticked" and label:
                        ticked_labels.append(label)
        for resp in page.get("responses", []) or []:
            if not isinstance(resp, dict):
                continue
            rsec = (resp.get("section") or "").strip().lower()
            if rsec == "surgeries/major events":
                for q in resp.get("questions", []) or []:
                    if not isinstance(q, dict):
                        continue
                    qtext = (q.get("question") or "").strip()
                    ans = q.get("answer")
                    if ans is None or str(ans).strip() == "":
                        continue
                    qa_pairs.append((qtext, str(ans).strip()))

    lines = []
    if ticked_labels:
        lines.append("Ticked Events: " + ", ".join(ticked_labels))
    for q, a in qa_pairs:
        lines.append(f"{q}: {a}")
    return "\n".join(lines)

def _populate_major_events(driver: WebDriver, summary_text: str, timeout: int = 15) -> bool:
    """Open the major events editor, populate textarea, and save."""
    if not summary_text.strip():
        return False
    wait = WebDriverWait(driver, timeout)
    # Dismiss any popups before starting
    _dismiss_any_popups(driver)
    add_mode_entered = False
    # Try main add button, fallback to edit button
    add_btn = None
    try:
        section_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-element='events-section']")))
        _dismiss_any_popups(driver)
        try:
            add_btn = section_container.find_element(By.CSS_SELECTOR, "[data-element='past-medical-history-field-add-button']")
        except Exception:
            add_btn = section_container.find_element(By.CSS_SELECTOR, "[data-element='past-medical-history-field-item-0']")
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_btn)
        except Exception:
            pass
        _dismiss_any_popups(driver)
        try:
            add_btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", add_btn)
        add_mode_entered = True
    except Exception:
        return False

    # Text area (prefer events-detail-text-area, fallback to family-health-history-text-area)
    textarea = None
    candidates = [
        "[data-element='events-detail-text-area']",
        "[data-element='family-health-history-text-area']",
    ]
    for css_sel in candidates:
        try:
            textarea = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_sel)))
            if textarea:
                break
        except Exception:
            continue
    if not textarea:
        return False
    _dismiss_any_popups(driver)
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", textarea)
    except Exception:
        pass
    try:
        textarea.clear()
    except Exception:
        try:
            textarea.send_keys(Keys.CONTROL, 'a')
            textarea.send_keys(Keys.DELETE)
        except Exception:
            pass
    try:
        textarea.send_keys(summary_text)
        # Trigger blur to ensure UI enables save button
        driver.execute_script("arguments[0].blur();", textarea)
    except Exception:
        return False

    # Save button
    _dismiss_any_popups(driver)
    try:
        save_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-element='btn-save']")))
    except Exception:
        return False
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_btn)
    except Exception:
        pass
    try:
        save_btn.click()
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", save_btn)
        except Exception:
            return False
    try:
        WebDriverWait(driver, 5).until(
            lambda d: (not save_btn.is_displayed()) or (not save_btn.is_enabled())
        )
    except Exception:
        try:
            _wait_for_data_load(driver, timeout=5)
        except Exception:
            pass
    return True

import logging
from typing import Optional, List, Dict
import time
import os
import shutil
from pathlib import Path
import json
from automation.extraction import run_intake_extractor

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys

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

            try:
                # Use a short timeout on pendingdocuments so we can fall back quickly
                clicked = _click_first_intake_document_type(driver, timeout=4)
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


def navigate_after_login(driver: WebDriver, url: Optional[str] = None, date_offset_days: int = -1, staging_dir: Optional[Path] = None) -> None:
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
            patient_id = _extract_patient_id(href)
            # Build timeline URL (pending documents) from summary URL before opening
            timeline_href = _to_timeline_url(href)
            LOGGER.info("[%s/%s] Opening patient timeline link: %s", idx, len(links), timeline_href)
            driver.get(timeline_href)
            _wait_for_data_load(driver, timeout=30)

            # Click the first occurrence of an 'intake' document-type entry if present
            try:
                clicked = _click_first_intake_document_type(driver, timeout=4)
                if clicked:
                    LOGGER.info("Clicked first 'intake' document-type link.")
                    try:
                        dest_pdf = _download_intake_document_if_available(driver, timeout=15, staging_dir=staging_dir, patient_id=patient_id)
                        if dest_pdf:
                            LOGGER.info("Downloaded and moved intake PDF to: %s", dest_pdf)
                            # Run extractor to produce <patientId>-intake-details.json and log
                            if patient_id and staging_dir:
                                output_json = staging_dir / f"{patient_id}-intake-details.json"
                                log_file = staging_dir / f"{patient_id}-intake-log.txt"
                                run_intake_extractor(dest_pdf, output_json, log_file)
                        else:
                            LOGGER.info("Download button [data-element='download-doc-btn'] not found or not clickable.")
                    except Exception:
                        LOGGER.debug("Error attempting to click download button.", exc_info=True)
                else:
                    LOGGER.info("No 'intake' document-type link found in pending documents; trying signed documents view.")
                    # Fallback: try the signed documents timeline
                    signed_href = _to_timeline_url_with_view(href, 'signeddocuments')
                    LOGGER.info("Opening patient signed documents timeline link: %s", signed_href)
                    driver.get(signed_href)
                    _wait_for_data_load(driver, timeout=30)
                    try:
                        clicked2 = _click_first_intake_document_type(driver, timeout=20)
                        if clicked2:
                            LOGGER.info("Clicked first 'intake' document-type link in signed documents view.")
                            try:
                                dest_pdf2 = _download_intake_document_if_available(driver, timeout=15, staging_dir=staging_dir, patient_id=patient_id)
                                if dest_pdf2:
                                    LOGGER.info("Downloaded and moved intake PDF to (signed view): %s", dest_pdf2)
                                    if patient_id and staging_dir:
                                        output_json2 = staging_dir / f"{patient_id}-intake-details.json"
                                        log_file2 = staging_dir / f"{patient_id}-intake-log.txt"
                                        run_intake_extractor(dest_pdf2, output_json2, log_file2)
                                else:
                                    LOGGER.info("Download button not found/clickable in signed documents view.")
                            except Exception:
                                LOGGER.debug("Error attempting to click download button in signed documents view.", exc_info=True)
                        else:
                            LOGGER.info("No 'intake' document-type link found in signed documents view either.")
                    except Exception:
                        LOGGER.debug("Error while attempting to click 'intake' in signed documents view.", exc_info=True)
            except Exception:
                LOGGER.debug("Error while attempting to click 'intake' document-type link.", exc_info=True)

            # After processing (whether or not an intake PDF was found), return to the original summary page
            returned_to_summary = False
            try:
                if href:
                    LOGGER.info("Returning to patient summary page: %s", href)
                    driver.get(href)
                    _wait_for_data_load(driver, timeout=30)
                    # Attempt to dismiss any popups/modals that might obscure form fields
                    try:
                        dismissed = _dismiss_any_popups(driver)
                        if dismissed:
                            LOGGER.info("Dismissed %s popup/modal element(s) on summary load.", dismissed)
                    except Exception:
                        LOGGER.debug("Error while attempting to dismiss popups after summary load.", exc_info=True)
                    returned_to_summary = True
            except Exception:
                LOGGER.debug("Failed to return to summary page for %s; continuing.", href, exc_info=True)

            # Populate Family History, Social History, Major Events, Ongoing Medical Problems, Nutrition History (only once per patient)
            if returned_to_summary and staging_dir and patient_id:
                intake_json = staging_dir / f"{patient_id}-intake-details.json"
                if intake_json.exists():
                    # Family History
                    try:
                        fam_text = _build_family_history_summary(intake_json)
                        LOGGER.debug("Family History summary for patient %s:\n%s", patient_id, fam_text)
                        if fam_text:
                            if _populate_family_history(driver, fam_text):
                                LOGGER.info("Filled family history text area for patient %s", patient_id)
                            else:
                                LOGGER.info("Family history UI elements not found / not filled for patient %s", patient_id)
                    except Exception:
                        LOGGER.debug("Error while building / populating family history summary for %s", patient_id, exc_info=True)
                    # Social History
                    try:
                        social_text = _build_social_history_summary(intake_json)
                        LOGGER.debug("Social History summary for patient %s:\n%s", patient_id, social_text)
                        if social_text:
                            if _populate_social_history(driver, social_text):
                                LOGGER.info("Filled social history text area for patient %s", patient_id)
                            else:
                                LOGGER.info("Social history UI elements not found / not filled for patient %s", patient_id)
                    except Exception:
                        LOGGER.debug("Error while building / populating social history summary for %s", patient_id, exc_info=True)
                    # Major Events
                    try:
                        major_events_text = _build_major_events_summary(intake_json)
                        LOGGER.debug("Major Events summary for patient %s:\n%s", patient_id, major_events_text)
                        if major_events_text:
                            if _populate_major_events(driver, major_events_text):
                                LOGGER.info("Filled major events text area for patient %s", patient_id)
                            else:
                                LOGGER.info("Major events UI elements not found / not filled for patient %s", patient_id)
                    except Exception:
                        LOGGER.debug("Error while building / populating major events summary for %s", patient_id, exc_info=True)
                    # Ongoing Medical Problems
                    try:
                        ongoing_medical_text = _build_ongoing_medical_problems_summary(intake_json)
                        LOGGER.debug("Ongoing Medical Problems summary for patient %s:\n%s", patient_id, ongoing_medical_text)
                        if ongoing_medical_text:
                            if _populate_ongoing_medical_problems(driver, ongoing_medical_text):
                                LOGGER.info("Filled ongoing medical problems text area for patient %s", patient_id)
                            else:
                                LOGGER.info("Ongoing medical problems UI elements not found / not filled for patient %s", patient_id)
                    except Exception:
                        LOGGER.debug("Error while building / populating ongoing medical problems summary for %s", patient_id, exc_info=True)
                    # Nutrition History
                    try:
                        nutrition_text = _build_nutrition_history_summary(intake_json)
                        LOGGER.info("Nutrition History summary for patient %s: %r", patient_id, nutrition_text)
                        if nutrition_text:
                            if _populate_nutrition_history(driver, nutrition_text):
                                LOGGER.info("Filled nutrition history text area for patient %s", patient_id)
                            else:
                                LOGGER.info("Nutrition history UI elements not found / not filled for patient %s", patient_id)
                        else:
                            LOGGER.info("Nutrition History summary is empty for patient %s", patient_id)
                    except Exception:
                        LOGGER.debug("Error while building / populating nutrition history summary for %s", patient_id, exc_info=True)
        except Exception:
            LOGGER.debug("Error opening patient link: %s", href, exc_info=True)

    if not url:
        LOGGER.info("No post-login URL provided; staying on current page.")
        return
    LOGGER.info("Navigating to %s", url)
    driver.get(url)


def _to_timeline_url(href: str) -> str:
    """Convert a patient 'summary' route to 'timeline/pendingdocuments' while preserving query/fragment structure."""
    return _to_timeline_url_with_view(href, 'pendingdocuments')


def _to_timeline_url_with_view(href: str, view: str) -> str:
    """Convert a patient 'summary' route to 'timeline/<view>' while preserving query/fragment structure.

    Supports SPA hash routes where the PF route is in the fragment and standard path routes.
    """
    try:
        from urllib.parse import urlparse, urlunparse, unquote, quote
        parsed = urlparse(href)
        frag = unquote(parsed.fragment or "")
        path = unquote(parsed.path or "")

        def replace_trailing_summary(s: str) -> str:
            s_main, sep, q = s.partition("?")
            s_main = s_main.rstrip("/")
            if s_main.endswith("summary"):
                s_main = s_main[: -len("summary")] + f"timeline/{view}"
            return s_main + (sep + q if sep else "")

        if "/PF/charts/patients/" in frag:
            new_frag = replace_trailing_summary(frag)
            return urlunparse(parsed._replace(fragment=quote(new_frag, safe="/:?=&")))
        if "/PF/charts/patients/" in path:
            new_path = replace_trailing_summary(path)
            return urlunparse(parsed._replace(path=quote(new_path, safe="/:?=&")))
        # Fallback: naive string replace at end
        if href.rstrip("/").endswith("summary"):
            return href[: -len("summary")] + f"timeline/{view}"
    except Exception:
        pass
    return href


def _print_if_intake_in_timeline_events(driver: WebDriver, timeout: int = 20) -> bool:
    """Scan the timeline events table for 'intake' in the second column; if present,
    print the hyperlink from the first column of that row to the console.

    Returns True if an 'intake' row is found (and hyperlink printed when available); else False.
    """
    wait = WebDriverWait(driver, timeout)
    table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-element='timeline-events-table']")))
    try:
        rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
        for r in rows:
            cells = r.find_elements(By.CSS_SELECTOR, "td")
            if len(cells) >= 2:
                txt = (cells[1].text or "").strip().lower()
                if "intake" in txt:
                    # Try to extract hyperlink from the first column of this row
                    href_printed = False
                    try:
                        link_el = cells[0].find_element(By.CSS_SELECTOR, "a[href]")
                        href = link_el.get_attribute("href") or ""
                        if href:
                            print(href)
                            href_printed = True
                    except Exception:
                        LOGGER.debug("No hyperlink found in first column of the 'intake' row.", exc_info=True)
                    if not href_printed:
                        print("Found 'intake' in timeline events (second column), but no hyperlink in first column.")
                    return True
    except Exception:
        LOGGER.debug("Error while scanning timeline events table rows.", exc_info=True)
    return False


def _click_first_intake_document_type(driver: WebDriver, timeout: int = 20) -> bool:
    """Within timeline events table, find the first element with
    data-element="document-type" and classes "text-color-link text-truncate"
    whose text contains 'intake' (case-insensitive), then click it.

    Returns True if clicked; else False.
    """
    wait = WebDriverWait(driver, timeout)
    # Ensure table exists
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-element='timeline-events-table']")))
    # XPath to find first matching element inside the table
    intake_xpath = (
        "//*[@data-element='timeline-events-table']"
        "//*[ @data-element='document-type'"
        " and contains(concat(' ', normalize-space(@class), ' '), ' text-color-link ')"
        " and contains(concat(' ', normalize-space(@class), ' '), ' text-truncate ')"
        " and contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'intake')"
        "][1]"
    )
    try:
        el = wait.until(EC.element_to_be_clickable((By.XPATH, intake_xpath)))
    except TimeoutException:
        return False
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
    except Exception:
        pass
    try:
        el.click()
    except Exception:
        driver.execute_script("arguments[0].click();", el)
    _wait_for_data_load(driver, timeout=30)
    return True


def _download_intake_document_if_available(driver: WebDriver, timeout: int = 15, staging_dir: Optional[Path] = None, patient_id: Optional[str] = None) -> Optional[Path]:
    """Click the download button for the intake document if present.

    Looks for [data-element='download-doc-btn'] and attempts to click it. Returns True if a click was triggered.
    """
    wait = WebDriverWait(driver, timeout)
    try:
        btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-element='download-doc-btn']")))
    except TimeoutException:
        return None
    # Clean Downloads of old intake*.pdf files before triggering a new download
    downloads_dir = _get_downloads_dir()
    try:
        _cleanup_old_intake_pdfs(downloads_dir)
    except Exception:
        LOGGER.debug("Failed to clean up old intake PDFs in Downloads.", exc_info=True)
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
    except Exception:
        pass
    try:
        btn.click()
    except Exception:
        driver.execute_script("arguments[0].click();", btn)
    # Wait for the download to complete and move it to staging if provided
    try:
        downloaded = _wait_for_intake_pdf(downloads_dir, max_wait=40)
        if downloaded and staging_dir:
            try:
                staging_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            target_name = _safe_patient_filename(patient_id) if patient_id else downloaded.name
            dest = _unique_destination(staging_dir, target_name)
            shutil.move(str(downloaded), str(dest))
            LOGGER.info("Moved downloaded file to staging: %s", dest)
            return dest
    except Exception:
        LOGGER.debug("Error while waiting/moving downloaded intake file.", exc_info=True)
    return None


def _get_downloads_dir() -> Path:
    # Default to user's Downloads directory
    home = Path(os.path.expanduser("~"))
    downloads = home / "Downloads"
    return downloads


def _cleanup_old_intake_pdfs(downloads_dir: Path) -> None:
    if not downloads_dir.exists():
        return
    for p in downloads_dir.glob("*"):
        name = p.name.lower()
        if name.startswith("intake") and name.endswith(".pdf"):
            try:
                p.unlink(missing_ok=True)
            except Exception:
                continue


def _wait_for_intake_pdf(downloads_dir: Path, max_wait: int = 40) -> Optional[Path]:
    """Wait until an intake*.pdf appears in Downloads (and is not a temp .crdownload)."""
    end = time.time() + max_wait
    candidate: Optional[Path] = None
    while time.time() < end:
        pdfs = [p for p in downloads_dir.glob("*.pdf") if p.name.lower().startswith("intake")]
        if pdfs:
            # Ensure no .crdownload temp for this file
            candidate = sorted(pdfs, key=lambda x: x.stat().st_mtime, reverse=True)[0]
            crdl = candidate.with_suffix(candidate.suffix + ".crdownload")
            if not crdl.exists():
                return candidate
        time.sleep(0.5)
    return candidate


def _unique_destination(folder: Path, filename: str) -> Path:
    dest = folder / filename
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    i = 1
    while True:
        cand = folder / f"{stem}({i}){suffix}"
        if not cand.exists():
            return cand
        i += 1


def _extract_patient_id(href: str) -> Optional[str]:
    """Extract the patient identifier from a PF charts URL.

    Supports URLs where the PF route is in the fragment (after #) or in the path.
    Returns the segment after '/PF/charts/patients/' up to the next '/'.
    """
    try:
        from urllib.parse import urlparse, unquote
        parsed = urlparse(href)
        frag = unquote(parsed.fragment or "")
        path = unquote(parsed.path or "")
        source = frag if "/PF/charts/patients/" in frag else path
        marker = "/PF/charts/patients/"
        if marker in source:
            after = source.split(marker, 1)[1]
            # after could be like '<id>/summary' or '<id>'
            parts = [p for p in after.split("/") if p]
            if parts:
                # Basic sanitize: allow alphanum, dash
                import re
                pid = parts[0]
                pid = re.sub(r"[^A-Za-z0-9\-]", "", pid)
                return pid or None
    except Exception:
        pass
    return None


def _safe_patient_filename(patient_id: str) -> str:
    """Return a safe file name '<patient_id>.pdf' using a conservative charset."""
    import re
    pid = re.sub(r"[^A-Za-z0-9\-]", "", patient_id or "")
    if not pid:
        return "intake.pdf"
    return f"{pid}.pdf"


def _dismiss_any_popups(driver: WebDriver, timeout: int = 5) -> int:
    """Attempt to close/dismiss any transient popups or modals that may appear after navigation.

    Heuristics:
      - Look for elements with common close selectors (data-element variants, role=dialog buttons, aria-label patterns).
      - Attempt click (normal then JS) and count successes.
      - Suppress errors; return number of elements we attempted to dismiss successfully.
    """
    potential_selectors = [
        "[data-element='close-modal']",
        "[data-element='modal-close']",
        "button.close",
        "button[aria-label='Close']",
        "[data-element='btn-dismiss']",
        "[data-element='popup-dismiss']",
        "[data-element='notification-dismiss']",
        "div.modal button[type='button'] span[class*='close']",
    ]
    dismissed = 0
    try:
        for sel in potential_selectors:
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, sel)
            except Exception:
                continue
            for btn in buttons:
                try:
                    if not btn.is_displayed():
                        continue
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    except Exception:
                        pass
                    try:
                        btn.click()
                    except Exception:
                        try:
                            driver.execute_script("arguments[0].click();", btn)
                        except Exception:
                            continue
                    dismissed += 1
                except Exception:
                    continue
    except Exception:
        pass
    return dismissed


# Extraction logic has been moved to automation.extraction.run_intake_extractor


# ---------------- Family History Summary Helpers -----------------
def _build_family_history_summary(intake_json: Path) -> str:
    """Build a concise family history summary from the intake JSON file.

    Strategy:
      - Locate response blocks whose section name contains 'FAMILY HISTORY'.
      - Extract question/answer pairs.
      - Group consecutive pairs (Age, Medical Conditions) for each relative when possible.
    Fallback: list each answered question on its own line.
    """
    import logging
    logger = logging.getLogger(__name__)
    try:
        data = json.loads(intake_json.read_text(encoding="utf-8", errors="ignore") or "{}")
    except Exception:
        logger.debug(f"[FamilyHistory] Failed to read or parse {intake_json}")
        return ""

    pages = data.get("pages") or []
    qa_pairs: List[Dict[str, str]] = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        responses = page.get("responses", []) or []
        for resp in responses:
            if not isinstance(resp, dict):
                continue
            section_name = (resp.get("section") or "").strip()
            if section_name and "family" in section_name.lower() and "history" in section_name.lower():
                for q in resp.get("questions", []) or []:
                    if not isinstance(q, dict):
                        continue
                    qtext = (q.get("question") or "").strip()
                    ans = q.get("answer")
                    if ans is None:
                        continue
                    ans_s = str(ans).strip()
                    if not ans_s:
                        continue
                    qa_pairs.append({"q": qtext, "a": ans_s})
    logger.debug(f"[FamilyHistory] Extracted {len(qa_pairs)} Q/A pairs from {intake_json}")
    if not qa_pairs:
        logger.debug(f"[FamilyHistory] No family history Q/A pairs found in {intake_json}")
        return ""

    summary_lines: List[str] = []
    used = set()
    for i, pair in enumerate(qa_pairs):
        if i in used:
            continue
        q = pair["q"].strip()
        a = pair["a"]
        lower_q = q.lower()
        if lower_q.endswith(" age"):
            base = q[:-4].strip()
            conditions = None
            for j in range(i + 1, len(qa_pairs)):
                if j in used:
                    continue
                nq_raw = qa_pairs[j]["q"].strip()
                nq = nq_raw.lower()
                if nq.endswith(" age") and nq_raw[:-4].strip() == base:
                    break
                if "medical" in nq and "condition" in nq:
                    conditions = qa_pairs[j]["a"]
                    used.add(j)
                    break
            if conditions:
                summary_lines.append(f"{base}: Age {a}; Conditions: {conditions}")
            else:
                summary_lines.append(f"{base}: Age {a}")
            used.add(i)
        elif "medical" in lower_q and "condition" in lower_q:
            summary_lines.append(f"{q}: {a}")
            used.add(i)
        else:
            summary_lines.append(f"{q}: {a}")
            used.add(i)
    logger.debug(f"[FamilyHistory] Summary for {intake_json}: {summary_lines}")
    return "\n".join(summary_lines)


def _populate_family_history(driver: WebDriver, summary_text: str, timeout: int = 15) -> bool:
    """Open the family history editor, populate textarea, and save.

    Returns True if we believe the operation succeeded, else False.
    """
    if not summary_text.strip():
        return False
    wait = WebDriverWait(driver, timeout)
    # Dismiss any popups before starting
    _dismiss_any_popups(driver)
    add_mode_entered = False
    # Primary approach: click the explicit "add" button
    try:
        add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-element='add-family-history-button']")))
        _dismiss_any_popups(driver)
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_btn)
        except Exception:
            pass
        _dismiss_any_popups(driver)
        try:
            add_btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", add_btn)
        add_mode_entered = True
    except Exception:
        # Fallback: existing family history text container (view mode) we can click to edit
        try:
            view_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-element='family-history-text']")))
            _dismiss_any_popups(driver)
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", view_el)
            except Exception:
                pass
            _dismiss_any_popups(driver)
            try:
                view_el.click()
            except Exception:
                driver.execute_script("arguments[0].click();", view_el)
            add_mode_entered = True
        except Exception:
            # Neither the add button nor the view text could be interacted with
            return False

    # Text area
    _dismiss_any_popups(driver)
    try:
        textarea = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-element='family-health-history-text-area']")))
    except Exception:
        return False
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", textarea)
    except Exception:
        pass
    try:
        textarea.clear()
    except Exception:
        # fallback to select-all delete
        try:
            textarea.send_keys(Keys.CONTROL, 'a')
            textarea.send_keys(Keys.DELETE)
        except Exception:
            pass
    try:
        textarea.send_keys(summary_text)
        # Trigger blur to ensure UI enables save button
        driver.execute_script("arguments[0].blur();", textarea)
    except Exception:
        return False

    # Save button
    _dismiss_any_popups(driver)
    try:
        save_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-element='btn-save']")))
    except Exception:
        return False
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_btn)
    except Exception:
        pass
    try:
        save_btn.click()
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", save_btn)
        except Exception:
            return False

    # Post-save: wait briefly for either button to disable/disappear or for spinner inactivity
    try:
        WebDriverWait(driver, 5).until(
            lambda d: (not save_btn.is_displayed()) or (not save_btn.is_enabled())
        )
    except Exception:
        # Fallback to generic data load wait (non-fatal if it times out)
        try:
            _wait_for_data_load(driver, timeout=5)
        except Exception:
            pass
    return True


def _build_social_history_summary(intake_json: Path) -> str:
    """Build social history summary with required fields.

    Fixed ordered categories:
      Tobacco
      Alcohol
      Caffeine
      Exercise
    Then (conditionally):
      Children (only if '# of Children' checkbox is ticked AND a corresponding answer exists)
      Occupation (only if a non-empty answer exists)

    Formatting:
      <Category>: Yes|No (Metric: value; Metric2: value ...)
      Children: <value>
      Occupation: <value>
    """
    import logging
    logger = logging.getLogger(__name__)
    try:
        data = json.loads(intake_json.read_text(encoding="utf-8", errors="ignore") or "{}")
    except Exception:
        logger.debug(f"[SocialHistory] Failed to read or parse {intake_json}")
        return ""

    pages = data.get("pages") or []
    categories = {
        "Tobacco": {"yes": False, "answers": {}, "explicit": None, "answered_questions": 0},
        "Alcohol": {"yes": False, "answers": {}, "explicit": None, "answered_questions": 0},
        "Caffeine": {"yes": False, "answers": {}, "explicit": None, "answered_questions": 0},
        "Exercise": {"yes": False, "answers": {}, "explicit": None, "answered_questions": 0},
    }

    def _is_yes_label(lbl: str) -> bool:
        l = lbl.lower().strip()
        return l == "yes" or l.startswith("yes") or (l.startswith("y") and len(l) <= 3)

    def _is_no_label(lbl: str) -> bool:
        l = lbl.lower().strip()
        return l == "no" or l.startswith("no") or (l.startswith("n") and len(l) <= 3)
    children_checkbox_ticked = False
    children_answer: str | None = None
    occupation_answer: str | None = None
    logger.debug(f"[SocialHistory] Starting extraction for {intake_json}")

    # Pass 1: sections (checkbox states)
    for page in pages:
        if not isinstance(page, dict):
            continue
        sections = page.get("sections", []) or []
        for section in sections:
            if not isinstance(section, dict):
                continue
            sec_name = (section.get("section") or "").strip()
            if not sec_name:
                continue
            sec_key = None
            for k in categories.keys():
                if sec_name.lower() == k.lower():
                    sec_key = k
                    break
            if sec_key:
                cbox_list = section.get("checkboxes", []) or []
                for cb in cbox_list:
                    if not isinstance(cb, dict):
                        continue
                    label_raw = (cb.get("label") or "").strip()
                    status = (cb.get("status") or "").lower()
                    if _is_yes_label(label_raw) and status == "ticked":
                        categories[sec_key]["yes"] = True
                        categories[sec_key]["explicit"] = True
                        logger.debug(f"[SocialHistory] {sec_key} checkbox YES detected: {cb}")
                    elif _is_no_label(label_raw) and status == "ticked" and not categories[sec_key]["yes"]:
                        categories[sec_key]["yes"] = False
                        categories[sec_key]["explicit"] = False
                        logger.debug(f"[SocialHistory] {sec_key} checkbox NO detected: {cb}")
                    if label_raw == "# of Children" and status == "ticked":
                        children_checkbox_ticked = True

    # Pass 2: responses (quantitative answers)
    for page in pages:
        if not isinstance(page, dict):
            continue
        responses = page.get("responses", []) or []
        for resp in responses:
            if not isinstance(resp, dict):
                continue
            rsec = (resp.get("section") or "").strip()
            questions = resp.get("questions", []) or []
            for q in questions:
                if not isinstance(q, dict):
                    continue
                qtext = (q.get("question") or "").strip()
                ans = q.get("answer")
                if ans is None:
                    continue
                sval = str(ans).strip()
                if not sval:
                    continue
                lower_q = qtext.lower()
                sec_key_r = None
                for k in categories.keys():
                    if rsec.lower() == k.lower():
                        sec_key_r = k
                        break
                if sec_key_r:
                    if sec_key_r == "Tobacco" and "packs/day" in lower_q and "Packs/Day" not in categories[sec_key_r]["answers"]:
                        categories[sec_key_r]["answers"]["Packs/Day"] = sval
                        logger.debug(f"[SocialHistory] Tobacco Packs/Day: {sval}")
                    elif sec_key_r == "Alcohol" and "drinks/week" in lower_q and "Drinks/Week" not in categories[sec_key_r]["answers"]:
                        categories[sec_key_r]["answers"]["Drinks/Week"] = sval
                        logger.debug(f"[SocialHistory] Alcohol Drinks/Week: {sval}")
                    elif sec_key_r == "Caffeine" and "cups/day" in lower_q and "Cups/Day" not in categories[sec_key_r]["answers"]:
                        categories[sec_key_r]["answers"]["Cups/Day"] = sval
                        logger.debug(f"[SocialHistory] Caffeine Cups/Day: {sval}")
                    elif sec_key_r == "Exercise":
                        if "days/week" in lower_q and "Days/Week" not in categories[sec_key_r]["answers"]:
                            categories[sec_key_r]["answers"]["Days/Week"] = sval
                            logger.debug(f"[SocialHistory] Exercise Days/Week: {sval}")
                        elif "occupation" in lower_q and not occupation_answer:
                            occupation_answer = sval
                            logger.debug(f"[SocialHistory] Occupation: {sval}")
                        elif ("# of children" in lower_q or ("please" in lower_q and "children" in lower_q)) and not children_answer:
                            children_answer = sval
                            logger.debug(f"[SocialHistory] Children: {sval}")
                    categories[sec_key_r]["answered_questions"] += 1
                else:
                    if "occupation" in lower_q and not occupation_answer:
                        occupation_answer = sval
                        logger.debug(f"[SocialHistory] Occupation: {sval}")
                    if ("# of children" in lower_q or ("please" in lower_q and "children" in lower_q)) and not children_answer:
                        children_answer = sval
                        logger.debug(f"[SocialHistory] Children: {sval}")

    # Inference: if a category has answered questions but no explicit checkbox state, treat as Yes
    for cat, info in categories.items():
        if info["explicit"] is None and info["answered_questions"] > 0:
            info["yes"] = True
            logger.debug(f"[SocialHistory] Inference | category={cat} | inferred=yes | answered_questions={info['answered_questions']}")

    lines: list[str] = []
    for cat in ["Tobacco", "Alcohol", "Caffeine", "Exercise"]:
        info = categories[cat]
        status = "Yes" if info["yes"] else "No"
        parts: list[str] = []
        if info["yes"]:
            for metric_key in ["Packs/Day", "Drinks/Week", "Cups/Day", "Days/Week"]:
                if metric_key in info["answers"]:
                    parts.append(f"{metric_key}: {info['answers'][metric_key]}")
        if parts:
            lines.append(f"{cat}: {status} ({'; '.join(parts)})")
        else:
            lines.append(f"{cat}: {status}")
    if children_checkbox_ticked and children_answer:
        lines.append(f"Children: {children_answer}")
        logger.debug(f"[SocialHistory] Children summary line: {children_answer}")
    if occupation_answer:
        lines.append(f"Occupation: {occupation_answer}")
        logger.debug(f"[SocialHistory] Occupation summary line: {occupation_answer}")
    logger.debug(f"[SocialHistory] Summary for {intake_json}: {lines}")
    return "\n".join(lines)


def _populate_social_history(driver: WebDriver, summary_text: str, timeout: int = 15) -> bool:
    """Open social/behavioral health editor, populate, save.

    Uses button [data-element='behavioral-health-field-add-button'] and expects a textarea analogous to family history field.
    If the same textarea selector is reused we can attempt a more specific one; for now reuse the family-health selector if social specific not found.
    """
    if not summary_text.strip():
        return False
    wait = WebDriverWait(driver, timeout)
    # Dismiss any popups before starting
    _dismiss_any_popups(driver)
    add_btn = None

    # Initial stabilization: ensure spinners gone before searching
    try:
        _wait_for_data_load(driver, timeout=10)
    except Exception:
        pass

    # Retry loop to find section + add button (helps right after another save or navigation)
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            section_container = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-element='socialHistory-section']"))
            )
            _dismiss_any_popups(driver)
            try:
                add_btn = section_container.find_element(By.CSS_SELECTOR, "[data-element='behavioral-health-field-add-button']")
            except Exception:
                add_btn = None
        except Exception:
            # Section not yet present; fall back to global attempt
            try:
                add_btn = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-element='behavioral-health-field-add-button']"))
                )
            except Exception:
                add_btn = None
        if add_btn:
            break
        # Brief poll wait before retrying
        time.sleep(0.5)
    editing_mode_entered = False
    path_used = ""  # add-button | existing-item
    if add_btn:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_btn)
        except Exception:
            pass
        _dismiss_any_popups(driver)
        try:
            add_btn.click()
            editing_mode_entered = True
            path_used = "add-button"
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", add_btn)
                editing_mode_entered = True
                path_used = "add-button"
            except Exception:
                editing_mode_entered = False
    if not editing_mode_entered:
        # Fallback: click existing first item to open editor
        try:
            section_container = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-element='socialHistory-section']"))
            )
            _dismiss_any_popups(driver)
            item = section_container.find_element(By.CSS_SELECTOR, "[data-element='behavioral-health-field-item-0']")
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
            except Exception:
                pass
            _dismiss_any_popups(driver)
            try:
                item.click()
                editing_mode_entered = True
                path_used = "existing-item"
            except Exception:
                try:
                    driver.execute_script("arguments[0].click();", item)
                    editing_mode_entered = True
                    path_used = "existing-item"
                except Exception:
                    editing_mode_entered = False
        except Exception:
            editing_mode_entered = False
    if not editing_mode_entered:
        return False

    # Try social specific textarea first (placeholder selector guess); fallback to family-health-history-text-area
    textarea = None
    candidates = [
        "[data-element='social-history-text-area']",
        "[data-element='behavioral-health-text-area']",
        "[data-element='family-health-history-text-area']",  # fallback reuse
    ]
    for css_sel in candidates:
        try:
            textarea = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_sel)))
            if textarea:
                break
        except Exception:
            continue
    if not textarea:
        return False
    _dismiss_any_popups(driver)
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", textarea)
    except Exception:
        pass
    try:
        textarea.clear()
    except Exception:
        try:
            textarea.send_keys(Keys.CONTROL, 'a')
            textarea.send_keys(Keys.DELETE)
        except Exception:
            pass
    # Log summary text before filling
    LOGGER.info("SocialHistory | summary_text before fill: %s", summary_text)
    try:
        driver.execute_script("arguments[0].focus();", textarea)
        textarea.send_keys(summary_text)
        # Dispatch input and change events to simulate real user input
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", textarea)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", textarea)
        time.sleep(0.2)
        # Log textarea value for diagnostics
        try:
            LOGGER.info("SocialHistory | textarea value after fill: %s", textarea.get_attribute("value"))
            # Fallback: if textarea value is still empty but summary_text is not, set via JS
            if summary_text.strip() and not textarea.get_attribute("value").strip():
                driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', { bubbles: true })); arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", textarea, summary_text)
                time.sleep(0.2)
                LOGGER.info("SocialHistory | textarea value after JS set: %s", textarea.get_attribute("value"))
        except Exception:
            pass
        # Trigger blur to ensure UI enables save button
        driver.execute_script("arguments[0].blur();", textarea)
    except Exception:
        return False

    # Save (social-specific button first, fallback to generic)
    _dismiss_any_popups(driver)
    save_btn = None
    save_selector_used = None
    save_selectors = [
        "[data-element='btn-social-health-save']",
        "[data-element='btn-save']",
    ]
    # Wait for save button to become enabled after text entry
    for sel in save_selectors:
        try:
            # Wait up to 5 seconds for button to be present
            save_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
            if save_btn:
                save_selector_used = sel
                # Wait up to 5 seconds for button to be enabled
                for _ in range(10):
                    _dismiss_any_popups(driver)
                    if save_btn.is_enabled() and not save_btn.get_attribute("disabled"):
                        break
                    time.sleep(0.5)
                if save_btn.is_enabled() and not save_btn.get_attribute("disabled"):
                    break
        except Exception:
            continue
    if not save_btn or not save_btn.is_enabled() or save_btn.get_attribute("disabled"):
        try:
            btn_html = save_btn.get_attribute("outerHTML") if save_btn else "(not found)"
        except Exception:
            btn_html = "(error getting HTML)"
        LOGGER.info(
            "SocialHistory | path=%s | action=aborted | reason=save-button-disabled | selector=%s | length=%s | btn_html=%s",
            path_used,
            save_selector_used,
            len(summary_text),
            btn_html,
        )
        return False
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_btn)
    except Exception:
        pass
    try:
        save_btn.click()
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", save_btn)
        except Exception:
            LOGGER.info(
                "SocialHistory | path=%s | saveClick=failed | selector=%s | length=%s | btn_html=%s",
                path_used,
                save_selector_used,
                len(summary_text),
                save_btn.get_attribute("outerHTML") if save_btn else "(not found)",
            )
            return False
    LOGGER.info(
        "SocialHistory | path=%s | saveClick=ok | selector=%s | length=%s",
        path_used,
        save_selector_used,
        len(summary_text),
    )
    # Post-save stabilization without fixed sleep
    try:
        WebDriverWait(driver, 5).until(
            lambda d: (not save_btn.is_displayed()) or (not save_btn.is_enabled())
        )
    except Exception:
        try:
            _wait_for_data_load(driver, timeout=5)
        except Exception:
            pass
    # Verification attempt: locate view container text and ensure snippet present; retry once if mismatch
    try:
        snippet = summary_text.strip().splitlines()[0][:25]
    except Exception:
        snippet = ""
    def _find_view_text() -> str:
        candidates_css = [
            "[data-element='behavioral-health-field-item-0']",
            "[data-element='social-history-text']",
        ]
        collected = []
        for css_sel in candidates_css:
            try:
                els = driver.find_elements(By.CSS_SELECTOR, css_sel)
                for e in els:
                    try:
                        t = (e.text or "").strip()
                        if t:
                            collected.append(t)
                    except Exception:
                        continue
            except Exception:
                continue
        return "\n".join(collected).strip()

    view_text = _find_view_text()
    if snippet and snippet not in view_text:
        LOGGER.info(
            "SocialHistory | path=%s | verify=missing-snippet | retry=1 | snippet='%s'",
            path_used,
            snippet,
        )
        # Retry once: reopen via existing item and reapply text
        try:
            section_container = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-element='socialHistory-section']"))
            )
            item = section_container.find_element(By.CSS_SELECTOR, "[data-element='behavioral-health-field-item-0']")
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
            except Exception:
                pass
            try:
                item.click()
            except Exception:
                try:
                    driver.execute_script("arguments[0].click();", item)
                except Exception:
                    pass
            # Re-find textarea
            textarea2 = None
            for css_sel in [
                "[data-element='social-history-text-area']",
                "[data-element='behavioral-health-text-area']",
                "[data-element='family-health-history-text-area']",
            ]:
                try:
                    textarea2 = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, css_sel))
                    )
                    if textarea2:
                        break
                except Exception:
                    continue
            if textarea2:
                # Clear existing text
                try:
                    textarea2.clear()
                except Exception:
                    try:
                        textarea2.send_keys(Keys.CONTROL, 'a')
                        textarea2.send_keys(Keys.DELETE)
                    except Exception:
                        pass
                # Re-enter summary text
                try:
                    LOGGER.info("SocialHistory | summary_text before fill (retry): %s", summary_text)
                    driver.execute_script("arguments[0].focus();", textarea2)
                    textarea2.send_keys(summary_text)
                    # Dispatch input and change events to simulate real user input
                    driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", textarea2)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", textarea2)
                    time.sleep(0.2)
                    # Log textarea value for diagnostics
                    try:
                        LOGGER.info("SocialHistory | textarea value after fill (retry): %s", textarea2.get_attribute("value"))
                        # Fallback: if textarea value is still empty but summary_text is not, set via JS
                        if summary_text.strip() and not textarea2.get_attribute("value").strip():
                            driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', { bubbles: true })); arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", textarea2, summary_text)
                            time.sleep(0.2)
                            LOGGER.info("SocialHistory | textarea value after JS set (retry): %s", textarea2.get_attribute("value"))
                    except Exception:
                        pass
                except Exception:
                    pass
                # Save again attempt
                save_btn2 = None
                for sel in save_selectors:
                    try:
                        save_btn2 = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                        )
                        if save_btn2:
                            break
                    except Exception:
                        continue
                if save_btn2:
                    try:
                        save_btn2.click()
                    except Exception:
                        try:
                            driver.execute_script("arguments[0].click();", save_btn2)
                        except Exception:
                            pass
                    try:
                        WebDriverWait(driver, 5).until(
                            lambda d: (not save_btn2.is_displayed()) or (not save_btn2.is_enabled())
                        )
                    except Exception:
                        pass
                    view_text = _find_view_text()
                    if snippet and snippet in view_text:
                        LOGGER.info(
                            "SocialHistory | path=%s | verify=success-after-retry | snippetFound=1",
                            path_used,
                        )
                    else:
                        LOGGER.info(
                            "SocialHistory | path=%s | verify=failed-after-retry | snippetFound=0",
                            path_used,
                        )
        except Exception:
            LOGGER.debug("SocialHistory verification retry failed.", exc_info=True)
    else:
        LOGGER.info(
            "SocialHistory | path=%s | verify=snippet-present | snippet='%s'",
            path_used,
            snippet,
        )
    return True

