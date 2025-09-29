from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException

LOGGER = logging.getLogger(__name__)


@dataclass
class Selector:
    type: str
    value: str

    def by(self) -> str:
        t = self.type.lower()
        if t == "css":
            return By.CSS_SELECTOR
        if t == "xpath":
            return By.XPATH
        if t == "id":
            return By.ID
        if t == "name":
            return By.NAME
        raise ValueError(f"Unsupported selector type: {self.type}")


@dataclass
class LoginSelectors:
    username: Selector
    password: Selector
    submit: Selector
    post_login_check: Optional[Selector] = None
    login_iframe: Optional[Selector] = None
    cookie_accept: Optional[Selector] = None


class LoginAutomation:
    def __init__(self, driver: WebDriver, base_url: str, selectors: LoginSelectors, timeout: int = 20):
        self.driver = driver
        self.base_url = base_url
        self.selectors = selectors
        self.wait = WebDriverWait(driver, timeout)
        self.short_wait = WebDriverWait(driver, 3)

    def _dump_debug(self, label: str) -> None:
        try:
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            out_dir = Path(".artifacts")
            out_dir.mkdir(parents=True, exist_ok=True)
            screenshot = out_dir / f"{ts}-{label}.png"
            html = out_dir / f"{ts}-{label}.html"
            self.driver.save_screenshot(str(screenshot))
            html.write_text(self.driver.page_source, encoding="utf-8")
            LOGGER.info("Saved debug screenshot and HTML: %s, %s", screenshot, html)
        except Exception:
            LOGGER.debug("Failed to save debug artifacts", exc_info=True)

    def is_logged_in(self) -> bool:
        """Quick check for a post-login element if configured (short timeout)."""
        if not self.selectors.post_login_check:
            return False
        try:
            self.short_wait.until(
                EC.presence_of_element_located(
                    (self.selectors.post_login_check.by(), self.selectors.post_login_check.value)
                )
            )
            LOGGER.debug("Post-login indicator found; assuming already logged in.")
            return True
        except Exception:
            return False

    def login_form_present(self) -> bool:
        try:
            self.short_wait.until(
                EC.presence_of_element_located((self.selectors.username.by(), self.selectors.username.value))
            )
            return True
        except Exception:
            return False

    def login(self, username: str, password: str) -> None:
        LOGGER.info("Opening %s", self.base_url)
        self.driver.get(self.base_url)

        # Handle cookie consent if configured
        if self.selectors.cookie_accept:
            try:
                btn = self.short_wait.until(
                    EC.element_to_be_clickable(
                        (self.selectors.cookie_accept.by(), self.selectors.cookie_accept.value)
                    )
                )
                btn.click()
                LOGGER.debug("Cookie consent accepted.")
            except Exception:
                LOGGER.debug("Cookie consent button not found or not clickable; continuing.")

        # Switch into iframe if login is inside one
        if self.selectors.login_iframe:
            try:
                frame_el = self.wait.until(
                    EC.presence_of_element_located(
                        (self.selectors.login_iframe.by(), self.selectors.login_iframe.value)
                    )
                )
                self.driver.switch_to.frame(frame_el)
                LOGGER.debug("Switched into login iframe.")
            except Exception:
                LOGGER.debug("Login iframe not present; continuing in default content.")

        # Prefer detecting login form first; only if not present, do a quick post-login check
        if self.login_form_present():
            LOGGER.debug("Login form detected; proceeding with credential entry.")
        elif self.is_logged_in():
            LOGGER.info("Already logged in; skipping credential entry.")
            return
        else:
            LOGGER.debug("Login form not detected yet; continuing and waiting for fields.")

        # Fill username
        u = self.wait.until(
            EC.element_to_be_clickable((self.selectors.username.by(), self.selectors.username.value))
        )
        u.clear()
        u.send_keys(username)

        # Fill password
        p = self.wait.until(
            EC.element_to_be_clickable((self.selectors.password.by(), self.selectors.password.value))
        )
        p.clear()
        p.send_keys(password)

        # Click submit
        s = self.wait.until(
            EC.element_to_be_clickable((self.selectors.submit.by(), self.selectors.submit.value))
        )
        s.click()

        # Final check (optional)
        # If we switched into an iframe, return to default content for post-login checks
        try:
            self.driver.switch_to.default_content()
        except Exception:
            pass

        # Detect common 2FA challenge page (Practice Fusion shows form#form2fa)
        try:
            twofa_el = self.short_wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form#form2fa"))
            )
            if twofa_el is not None:
                LOGGER.warning(
                    "Two-factor authentication challenge detected (form#form2fa). "
                    "Run without --headless to use your Default profile and trust the browser, "
                    "or enable 2FA handling to proceed."
                )
                self._dump_debug("twofa-detected")
                return
        except TimeoutException:
            # No 2FA form detected quickly; proceed to post-login check if configured
            pass

        if self.selectors.post_login_check:
            try:
                self.wait.until(
                    EC.presence_of_element_located(
                        (self.selectors.post_login_check.by(), self.selectors.post_login_check.value)
                    )
                )
                LOGGER.info("Login appears successful.")
            except TimeoutException:
                LOGGER.warning(
                    "Post-login indicator not found within timeout. Verify selectors or try non-headless to inspect."
                )
                self._dump_debug("post-login-timeout")
        else:
            LOGGER.info("Submitted login; consider adding a post_login_check selector for robust verification.")
