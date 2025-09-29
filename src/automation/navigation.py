from __future__ import annotations

import logging
from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver

LOGGER = logging.getLogger(__name__)


def navigate_after_login(driver: WebDriver, url: Optional[str] = None) -> None:
    if not url:
        LOGGER.info("No post-login URL provided; staying on current page.")
        return
    LOGGER.info("Navigating to %s", url)
    driver.get(url)
