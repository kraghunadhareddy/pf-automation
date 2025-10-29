# --- Preventive Care Summary Helper ---
from selenium.webdriver.remote.webdriver import WebDriver
from pathlib import Path
from datetime import datetime
from automation.ui_selectors import UI_SELECTORS
def build_preventive_care_summary(intake_json):
    """
    Extract summary from Preventive Care related sections for female patients only.
    Sections: 'PREGNANCY HISTORY/PREVENTATIVE CARE', 'PREVENTATIVE CARE'
    """
    from pathlib import Path
    sections_of_interest = [
        "PREGNANCY HISTORY/PREVENTATIVE CARE",
        "PREVENTATIVE CARE",
    ]
    try:
        if isinstance(intake_json, str) or isinstance(intake_json, Path):
            with open(intake_json, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = intake_json
    except Exception:
        return "No preventive care details found."

    lines = []
    for page in data.get("pages", []):
        for section in page.get("sections", []):
            sec_name = (section.get("section", "")).strip().upper()
            if sec_name in [s.upper() for s in sections_of_interest]:
                for q in section.get("questions", []):
                    question = q.get("question", "")
                    answer = q.get("answer")
                    if answer is not None and str(answer).strip():
                        lines.append(f"{question}: {answer}")
        for resp in page.get("responses", []):
            rsec = (resp.get("section", "")).strip().upper()
            if rsec in [s.upper() for s in sections_of_interest]:
                for q in resp.get("questions", []):
                    question = q.get("question", "")
                    answer = q.get("answer")
                    if answer is not None and str(answer).strip():
                        lines.append(f"{question}: {answer}")
    if not lines:
        return "No preventive care details found."
    return "\n".join(lines)

def populate_preventive_care(driver, summary_text, timeout=15):
    from automation.ui_selectors import UI_SELECTORS
    return populate_section_generic(driver, summary_text, "preventive_care", timeout)

def process_preventive_care_if_female(driver, intake_json, timeout=15):
    """
    If global GENDER_IS_FEMALE is True, extract and populate preventive care summary.
    """
    global GENDER_IS_FEMALE
    if GENDER_IS_FEMALE:
        summary = build_preventive_care_summary(intake_json)
        print(f"[PREVENTIVE] Summary for female patient: {summary}")
        filled = False
        if summary:
            filled = populate_preventive_care(driver, summary, timeout)
        print(f"[PREVENTIVE] UI action: {'Success' if filled else 'Failure'}")
    else:
        print("[PREVENTIVE] Skipped: Not a female patient.")
import json
from pathlib import Path

# Global gender flag
GENDER_IS_FEMALE = False

def detect_gender_from_intake(intake_json):
    """
    Detect gender from intake JSON.
    If any section or response is named 'Female Patient Information' (case-insensitive), return 'Female'.
    If any section or response is named 'Male Patient Information' (case-insensitive), return 'Male'.
    Returns None if not found.
    """
    try:
        if isinstance(intake_json, str) or isinstance(intake_json, Path):
            with open(intake_json, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = intake_json
    except Exception:
        return None
    gender_found = None
    for page in data.get("pages", []):
        for section in page.get("sections", []):
            sec_name = (section.get("section", "")).strip().lower()
            if sec_name == "female patient information":
                gender_found = "Female"
            elif sec_name == "male patient information":
                if gender_found != "Female":
                    gender_found = "Male"
        for resp in page.get("responses", []):
            rsec = (resp.get("section", "")).strip().lower()
            if rsec == "female patient information":
                gender_found = "Female"
            elif rsec == "male patient information":
                if gender_found != "Female":
                    gender_found = "Male"
    return gender_found

def set_global_gender_flag(intake_json):
    """
    Sets the global GENDER_IS_FEMALE flag based on intake JSON.
    """
    global GENDER_IS_FEMALE
    gender = detect_gender_from_intake(intake_json)
    GENDER_IS_FEMALE = (gender == "Female")
def _populate_family_history(driver, summary_text, timeout=15) -> bool:
    return populate_section_generic(driver, summary_text, "family_history", timeout)

def _populate_social_history(driver, summary_text, timeout=15) -> bool:
    return populate_section_generic(driver, summary_text, "social_history", timeout)

def _populate_major_events(driver, summary_text, timeout=15) -> bool:
    return populate_section_generic(driver, summary_text, "major_events", timeout)

def _populate_ongoing_medical_problems(driver, summary_text, timeout=15) -> bool:
    return populate_section_generic(driver, summary_text, "ongoing_medical_problems", timeout)

def _build_family_history_summary(intake_json):
    import json
    import sys
    print(f"[DEBUG] intake_json type: {type(intake_json)}, value: {intake_json}")
    sys.stdout.flush()
    try:
        if isinstance(intake_json, str) or isinstance(intake_json, Path):
            with open(intake_json, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = intake_json
    except Exception as e:
        print(f"[DEBUG] Error loading intake_json: {e}")
        sys.stdout.flush()
        return "No family history found."

    # Print all section names for debugging
    section_names = []
    for page in data.get("pages", []):
        for section in page.get("sections", []):
            section_names.append(section.get("section", "<no section key>"))
        for resp in page.get("responses", []):
            section_names.append(resp.get("section", "<no section key>"))
    print(f"[DEBUG] All section names found: {section_names}")
    sys.stdout.flush()

    family_sections = []
    # Search for FAMILY HISTORY in both sections and responses
    for page in data.get("pages", []):
        for section in page.get("sections", []):
            if section.get("section", "").strip().upper() == "FAMILY HISTORY":
                family_sections.append(section)
        for resp in page.get("responses", []):
            if resp.get("section", "").strip().upper() == "FAMILY HISTORY":
                family_sections.append(resp)

    if not family_sections:
        return "No family history found."

    print(f"[DEBUG] Raw family_sections: {family_sections}")
    sys.stdout.flush()
    lines = []
    for section in family_sections:
        # Extract questions/answers
        for q in section.get("questions", []):
            question = q.get("question", "")
            answer = q.get("answer")
            if answer is not None and str(answer).strip():
                lines.append(f"{question}: {answer}")
        # Extract ticked checkboxes
        for cb in section.get("checkboxes", []):
            label = cb.get("label", "")
            status = cb.get("status", "")
            if status.lower() == "ticked":
                lines.append(f"{label}")
    print(f"[DEBUG] Extracted family history lines: {lines}")
    sys.stdout.flush()
    return "\n".join(lines) if lines else "No family history details available."

def _build_social_history_summary(intake_json):
    import sys
    from pathlib import Path
    import json
    print(f"[DEBUG] intake_json type: {type(intake_json)}, value: {intake_json}")
    sys.stdout.flush()
    try:
        if isinstance(intake_json, str) or isinstance(intake_json, Path):
            with open(intake_json, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = intake_json
    except Exception as e:
        print(f"[DEBUG] Error loading intake_json: {e}")
        sys.stdout.flush()
        return "No social history found."

    section_names = []
    for page in data.get("pages", []):
        for section in page.get("sections", []):
            section_names.append(section.get("section", "<no section key>"))
        for resp in page.get("responses", []):
            section_names.append(resp.get("section", "<no section key>"))
    print(f"[DEBUG] All section names found: {section_names}")
    sys.stdout.flush()

    social_sections = []
    for page in data.get("pages", []):
        for section in page.get("sections", []):
            if section.get("section", "").strip().upper() == "SOCIAL HISTORY":
                social_sections.append(section)
        for resp in page.get("responses", []):
            if resp.get("section", "").strip().upper() == "SOCIAL HISTORY":
                social_sections.append(resp)

    if not social_sections:
        return "No social history found."

    print(f"[DEBUG] Raw social_sections: {social_sections}")
    sys.stdout.flush()
    lines = []
    for section in social_sections:
        # Extract questions/answers
        for q in section.get("questions", []):
            question = q.get("question", "")
            answer = q.get("answer")
            if answer is not None and str(answer).strip():
                lines.append(f"{question}: {answer}")
        # Extract ticked checkboxes
        for cb in section.get("checkboxes", []):
            label = cb.get("label", "")
            status = cb.get("status", "")
            if status.lower() == "ticked":
                lines.append(f"{label}")
    print(f"[DEBUG] Extracted social history lines: {lines}")
    sys.stdout.flush()
    return "\n".join(lines) if lines else "No social history details available."

def _build_major_events_summary(intake_json):
    import sys
    from pathlib import Path
    import json
    print(f"[DEBUG] intake_json type: {type(intake_json)}, value: {intake_json}")
    sys.stdout.flush()
    try:
        if isinstance(intake_json, str) or isinstance(intake_json, Path):
            with open(intake_json, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = intake_json
    except Exception as e:
        print(f"[DEBUG] Error loading intake_json: {e}")
        sys.stdout.flush()
        return "No major events found."

    section_names = []
    for page in data.get("pages", []):
        for section in page.get("sections", []):
            section_names.append(section.get("section", "<no section key>"))
        for resp in page.get("responses", []):
            section_names.append(resp.get("section", "<no section key>"))
    print(f"[DEBUG] All section names found: {section_names}")
    sys.stdout.flush()

    major_sections = []
    for page in data.get("pages", []):
        for section in page.get("sections", []):
            if section.get("section", "").strip().upper() == "SURGERIES/MAJOR EVENTS":
                major_sections.append(section)
        for resp in page.get("responses", []):
            if resp.get("section", "").strip().upper() == "SURGERIES/MAJOR EVENTS":
                major_sections.append(resp)

    if not major_sections:
        return "No major events found."

    print(f"[DEBUG] Raw major_sections: {major_sections}")
    sys.stdout.flush()
    lines = []
    for section in major_sections:
        # Extract questions/answers
        for q in section.get("questions", []):
            question = q.get("question", "")
            answer = q.get("answer")
            if answer is not None and str(answer).strip():
                lines.append(f"{question}: {answer}")
        # Extract ticked checkboxes
        for cb in section.get("checkboxes", []):
            label = cb.get("label", "")
            status = cb.get("status", "")
            if status.lower() == "ticked":
                lines.append(f"{label}")
    print(f"[DEBUG] Extracted major events lines: {lines}")
    sys.stdout.flush()
    return "\n".join(lines) if lines else "No major events details available."

def _build_social_history_summary(intake_json):
    """Aggregate Social History across Tobacco/Alcohol/Caffeine/Exercise sections and responses.

    Derives Yes/No from ticked checkboxes per category (treat "None"/"None/ NA" as No; any other ticked as Yes),
    and pulls metrics from responses (Packs/Day, Drinks/Week, Cups/Day, Days/Week). Also includes Children and
    Occupation when available.
    """
    import json, logging
    from pathlib import Path
    logger = logging.getLogger(__name__)
    # Load JSON from Path/str/dict
    try:
        if isinstance(intake_json, (str, Path)):
            with open(intake_json, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = intake_json
    except Exception:
        return ""

    pages = data.get("pages") or []
    # Categories scaffold
    categories = {
        "Tobacco": {"yes": None, "answers": {}, "explicit": None, "answered_questions": 0},
        "Alcohol": {"yes": None, "answers": {}, "explicit": None, "answered_questions": 0},
        "Caffeine": {"yes": None, "answers": {}, "explicit": None, "answered_questions": 0},
        "Exercise": {"yes": None, "answers": {}, "explicit": None, "answered_questions": 0},
    }
    occupation_answer = ""
    children_answer = ""
    children_checkbox_ticked = False

    def norm(name: str) -> str:
        return (name or "").strip().lower()

    def looks_like_none(label: str) -> bool:
        l = (label or "").strip().lower()
        return l in {"none", "none/ na", "none/na", "no", "n/a"}

    # Pass 1: sections with checkboxes determine explicit yes/no
    for page in pages:
        if not isinstance(page, dict):
            continue
        for section in page.get("sections", []) or []:
            if not isinstance(section, dict):
                continue
            sec = norm(section.get("section"))
            if sec in {"tobacco", "alcohol", "caffeine", "exercise"}:
                sec_key = sec.capitalize()
                any_non_none_ticked = False
                any_no_ticked = False
                any_yes_ticked = False
                for cb in section.get("checkboxes", []) or []:
                    if not isinstance(cb, dict):
                        continue
                    label = (cb.get("label") or "").strip()
                    status = (cb.get("status") or "").lower()
                    if status != "ticked":
                        continue
                    l = label.lower()
                    if l == "yes":
                        any_yes_ticked = True
                    elif l == "no" or looks_like_none(label):
                        any_no_ticked = True
                    else:
                        any_non_none_ticked = True
                # Priority: explicit Yes/No over other non-none ticks
                if any_yes_ticked:
                    categories[sec_key]["yes"] = True
                    categories[sec_key]["explicit"] = True
                elif any_no_ticked:
                    categories[sec_key]["yes"] = False
                    categories[sec_key]["explicit"] = False
                elif any_non_none_ticked:
                    categories[sec_key]["yes"] = True
                    categories[sec_key]["explicit"] = True

    # Pass 2: responses for metrics and additional signals
    for page in pages:
        if not isinstance(page, dict):
            continue
        for resp in page.get("responses", []) or []:
            if not isinstance(resp, dict):
                continue
            rsec = norm(resp.get("section"))
            for q in resp.get("questions", []) or []:
                if not isinstance(q, dict):
                    continue
                qtext = (q.get("question") or "").strip()
                sval = str(q.get("answer") or "").strip()
                if not sval:
                    continue
                lower_q = qtext.lower()
                # map section to category
                sec_key = None
                for k in categories.keys():
                    if rsec == k.lower():
                        sec_key = k
                        break
                if sec_key:
                    categories[sec_key]["answered_questions"] += 1
                    if sec_key == "Tobacco" and "packs/day" in lower_q and "Packs/Day" not in categories[sec_key]["answers"]:
                        categories[sec_key]["answers"]["Packs/Day"] = sval
                    elif sec_key == "Alcohol" and "drinks/week" in lower_q and "Drinks/Week" not in categories[sec_key]["answers"]:
                        categories[sec_key]["answers"]["Drinks/Week"] = sval
                    elif sec_key == "Caffeine" and "cups/day" in lower_q and "Cups/Day" not in categories[sec_key]["answers"]:
                        categories[sec_key]["answers"]["Cups/Day"] = sval
                    elif sec_key == "Exercise" and "days/week" in lower_q and "Days/Week" not in categories[sec_key]["answers"]:
                        categories[sec_key]["answers"]["Days/Week"] = sval
                    # an answered metric implies participation unless explicit No was set
                    if categories[sec_key]["explicit"] is None:
                        categories[sec_key]["yes"] = True
                # Regardless of section, capture these specifics
                if "occupation" in lower_q and not occupation_answer:
                    occupation_answer = sval
                if ("# of children" in lower_q or ("please" in lower_q and "children" in lower_q)) and not children_answer:
                    children_answer = sval

    # If category had answered questions but no explicit checkbox, treat as Yes
    for cat, info in categories.items():
        if info["explicit"] is None and info["answered_questions"] > 0 and info["yes"] is None:
            info["yes"] = True

    # Compose lines in fixed order
    lines = []
    for cat in ["Tobacco", "Alcohol", "Caffeine", "Exercise"]:
        info = categories[cat]
        if info["yes"] is None:
            # default to No if nothing was indicated
            info["yes"] = False
        status = "Yes" if info["yes"] else "No"
        parts = []
        for mk in ["Packs/Day", "Drinks/Week", "Cups/Day", "Days/Week"]:
            if mk in info["answers"]:
                parts.append(f"{mk}: {info['answers'][mk]}")
        if parts:
            lines.append(f"{cat}: {status} ({'; '.join(parts)})")
        else:
            lines.append(f"{cat}: {status}")
    if children_answer:
        lines.append(f"Children: {children_answer}")
    if occupation_answer:
        lines.append(f"Occupation: {occupation_answer}")
    return "\n".join(lines).strip()

def _build_nutrition_history_summary(intake_json: Path) -> str:
    """Summarize Nutrition History from intake JSON.

    Combines Q/A pairs from Nutrition-related sections/responses and any ticked checkbox labels
    (including Supplements) into a single multi-line summary.
    Accepts a Path to the JSON file or an already-loaded dict/str path.
    """
    # Load JSON flexibly (Path, str path, or dict)
    try:
        if isinstance(intake_json, (str, Path)):
            p = Path(intake_json)
            data = json.loads(p.read_text(encoding="utf-8", errors="ignore") or "{}")
        else:
            data = intake_json
    except Exception:
        return ""

    pages = data.get("pages") or []
    qa_lines: list[str] = []
    ticked: list[str] = []

    def is_nutrition_section(name: str) -> bool:
        n = (name or "").strip().lower()
        return (
            "nutrition" in n
            or "nutrition history" in n
            or "diet" in n
            or "supplement" in n
        )

    for page in pages:
        if not isinstance(page, dict):
            continue
        # Sections: collect ticked + possible embedded Q/A
        for section in page.get("sections", []) or []:
            if not isinstance(section, dict):
                continue
            sec_name = section.get("section") or ""
            if is_nutrition_section(sec_name):
                # Tick boxes
                for cb in section.get("checkboxes", []) or []:
                    if not isinstance(cb, dict):
                        continue
                    label = (cb.get("label") or "").strip()
                    status = (cb.get("status") or "").lower()
                    if status == "ticked" and label:
                        ticked.append(label)
                # Embedded questions (rare)
                for q in section.get("questions", []) or []:
                    if not isinstance(q, dict):
                        continue
                    qtext = (q.get("question") or "").strip()
                    ans = q.get("answer")
                    if ans is None or str(ans).strip() == "":
                        continue
                    qa_lines.append(f"{qtext}: {str(ans).strip()}")
        # Responses: primary Q/A live here
        for resp in page.get("responses", []) or []:
            if not isinstance(resp, dict):
                continue
            rsec = resp.get("section") or ""
            if is_nutrition_section(rsec):
                for q in resp.get("questions", []) or []:
                    if not isinstance(q, dict):
                        continue
                    qtext = (q.get("question") or "").strip()
                    ans = q.get("answer")
                    if ans is None or str(ans).strip() == "":
                        continue
                    qa_lines.append(f"{qtext}: {str(ans).strip()}")

    lines: list[str] = []
    if ticked:
        lines.append("Ticked: " + ", ".join(ticked))
    lines.extend(qa_lines)
    return "\n".join(lines).strip()

def _populate_nutrition_history(driver, summary_text, timeout=15) -> bool:
    """Open nutrition history editor, populate textarea, and save."""
    return populate_section_generic(driver, summary_text, "nutrition_history", timeout, debug_capture=_capture_nutrition_debug)

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
    return populate_section_generic(driver, summary_text, "ongoing_medical_problems", timeout)

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
            sec_name = (section.get("section") or "").strip().lower().replace("/", "").replace(" ", "")
            if sec_name == "surgeriesmajorevents":
                for cb in section.get("checkboxes", []) or []:
                    label = (cb.get("label") or "").strip()
                    status = (cb.get("status") or "").lower()
                    if status == "ticked" and label:
                        ticked_labels.append(label)
        for resp in page.get("responses", []) or []:
            if not isinstance(resp, dict):
                continue
            rsec = (resp.get("section") or "").strip().lower().replace("/", "").replace(" ", "")
            if rsec == "surgeriesmajorevents":
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
    return populate_section_generic(driver, summary_text, "major_events", timeout)

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
                # Minimal throttle to avoid flooding UI; we'll wait after the batch
                time.sleep(0.03)
            except StaleElementReferenceException as se:
                last_err = se
                time.sleep(0.05)
                continue
            except Exception as e:
                last_err = e
                LOGGER.debug("Step %s/%s: error clicking %s-day button", i + 1, steps, direction, exc_info=True)
                time.sleep(0.05)
        # Single consolidated wait after all clicks
        try:
            _wait_for_data_load(driver, timeout=timeout)
        except Exception:
            pass
        if last_err:
            LOGGER.debug("Date shift completed with last error: %s", repr(last_err))
        LOGGER.info("Date shift complete | offset=%s | attempted steps=%s", offset_days, steps)
    except TimeoutException:
        LOGGER.warning("Date picker button (id=date-picker-button) not present within %ss; skipping date shift.", timeout)
    except Exception:
        LOGGER.debug("Error while shifting date by offset.", exc_info=True)


def click_appointments_tab(driver: WebDriver, timeout: int = 8) -> None:
    """Ensure the 'Appointments' tab is active on the scheduler before date selection.

    Targets UI_SELECTORS['schedule_tabs']['appointments'] (data-element='scheduler-tab-0').
    If already active, no action is taken. Otherwise, clicks the tab and waits briefly for idle.
    """
    try:
        from automation.ui_selectors import UI_SELECTORS
        sel = (UI_SELECTORS.get("schedule_tabs") or {}).get("appointments")
        if not sel:
            return
        el = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
        try:
            cls = (el.get_attribute("class") or "").lower()
            if "active" in cls:
                LOGGER.info("Scheduler tab 'Appointments' already active.")
                return
        except Exception:
            pass
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
        except Exception:
            pass
        try:
            el.click()
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", el)
            except Exception:
                LOGGER.debug("Failed to click Appointments tab.", exc_info=True)
                return
        # brief idle wait
        try:
            _wait_for_data_load(driver, timeout=10)
        except Exception:
            pass
        LOGGER.info("Scheduler tab 'Appointments' clicked.")
    except TimeoutException:
        LOGGER.info("Appointments tab not found; continuing without switching.")
    except Exception:
        LOGGER.debug("Error while ensuring Appointments tab.", exc_info=True)


def print_patient_links_from_table(driver: WebDriver, timeout: int = 6) -> list[str]:
    from urllib.parse import urlparse, unquote
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
    except Exception as e:
        LOGGER.error(f"Unexpected error in patient link table wait: {e}", exc_info=True)
        return []

    links: list[str] = []
    try:
        anchors = driver.find_elements(By.CSS_SELECTOR, "table.data-table__grid a[href]")
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
    except Exception as e:
        LOGGER.error(f"Error while extracting patient links: {e}", exc_info=True)
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


def _to_timeline_url(href: str) -> str:
    """Convert a patient summary URL to the timeline (pending documents) URL."""
    # Example: /PF/charts/patients/<id>/summary -> /PF/charts/patients/<id>/timeline/pendingdocuments
    if href.endswith("/summary"):
        return href.replace("/summary", "/timeline/pendingdocuments")
    return href

def _to_timeline_url_with_view(href: str, view: str) -> str:
    """Convert a patient summary URL to the timeline URL for a specific view (e.g., signeddocuments)."""
    # Example: /PF/charts/patients/<id>/summary -> /PF/charts/patients/<id>/timeline/<view>
    if href.endswith("/summary"):
        return href.replace("/summary", f"/timeline/{view}")
    return href

def navigate_after_login(
    driver: WebDriver,
    url: Optional[str] = None,
    date_offset_days: int = -1,
    staging_dir: Optional[Path] = None,
    skip_click_schedule: bool = False,
    skip_tabs_and_date: bool = False,
) -> None:
    # Always attempt to click the 'Schedule' item once we believe we're logged in (unless already on it)
    if not skip_click_schedule:
        click_schedule(driver)

    # Ensure the Appointments tab and date as requested
    if not skip_tabs_and_date:
        # Appointments tab first per requested sequence
        click_appointments_tab(driver)
        # Toggle filter if needed
        ensure_filter_button_checked(driver)
        # Shift date when applicable
        select_relative_date_in_datepicker(driver, offset_days=date_offset_days)
    else:
        # Even if skipping tabs/date, ensure filter is on for consistent results
        ensure_filter_button_checked(driver)

    # After date change, collect patient chart links and print them
    links = print_patient_links_from_table(driver)
    if not isinstance(links, list):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] Patient links is not a list (type={type(links)}); setting to empty list.")
        links = []
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Found {len(links)} patients.")
    if links:
        patient_ids = [_extract_patient_id(href) for href in links]
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Patient IDs:")
        for pid in patient_ids:
            print(f"  {pid}")
        for idx, href in enumerate(links, start=1):
            patient_id = _extract_patient_id(href)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [PATIENT] {patient_id} | Start flow [{idx}/{len(links)}]")
            timeline_href = _to_timeline_url(href)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [NAV] {patient_id} | Opened timeline link: {timeline_href}")
            driver.get(timeline_href)
            _wait_for_data_load(driver, timeout=30)

            # Try pending view first
            found_in = None
            clicked = False
            try:
                clicked = _click_first_intake_document_type(driver, timeout=4)
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [DOC] {patient_id} | Intake document link clicked in pending: {'Success' if clicked else 'Failure'}")
                dest_pdf = None
                if clicked:
                    try:
                        dest_pdf = _download_intake_document_if_available(driver, timeout=15, staging_dir=staging_dir, patient_id=patient_id)
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [DOC] {patient_id} | Downloaded intake PDF: {'Success' if dest_pdf else 'Failure'}")
                        if dest_pdf and patient_id and staging_dir:
                            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [STAGING] {patient_id} | PDF moved to staging: {dest_pdf}")
                            output_json = staging_dir / f"{patient_id}-intake-details.json"
                            log_file = staging_dir / f"{patient_id}-intake-log.txt"
                            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [PARSER] {patient_id} | Starting PDF parser...")
                            parser_success = run_intake_extractor(dest_pdf, output_json, log_file)
                            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [PARSER] {patient_id} | PDF parser finished: {'Success' if parser_success else 'Failure'}")
                        found_in = "pending"
                    except Exception as e:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] {patient_id} | Download error: {e}")
                else:
                    # Try signed view if not found in pending
                    found_in = "signed"
                    signed_href = _to_timeline_url_with_view(href, 'signeddocuments')
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [NAV] {patient_id} | Tried signed documents view: {signed_href}")
                    driver.get(signed_href)
                    _wait_for_data_load(driver, timeout=30)
                    try:
                        clicked2 = _click_first_intake_document_type(driver, timeout=20)
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [DOC] {patient_id} | Intake document link clicked in signed: {'Success' if clicked2 else 'Failure'}")
                        dest_pdf = None
                        if clicked2:
                            try:
                                dest_pdf = _download_intake_document_if_available(driver, timeout=15, staging_dir=staging_dir, patient_id=patient_id)
                                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [DOC] {patient_id} | Downloaded intake PDF (signed): {'Success' if dest_pdf else 'Failure'}")
                                if dest_pdf and patient_id and staging_dir:
                                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [STAGING] {patient_id} | PDF moved to staging (signed): {dest_pdf}")
                                    output_json = staging_dir / f"{patient_id}-intake-details.json"
                                    log_file = staging_dir / f"{patient_id}-intake-log.txt"
                                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [PARSER] {patient_id} | Starting PDF parser (signed)...")
                                    parser_success = run_intake_extractor(dest_pdf, output_json, log_file)
                                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [PARSER] {patient_id} | PDF parser finished (signed): {'Success' if parser_success else 'Failure'}")
                            except Exception as e:
                                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] {patient_id} | Download error (signed): {e}")
                    except Exception as e:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] {patient_id} | Signed view download error: {e}")
            except Exception as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] {patient_id} | Intake document navigation error: {e}")

            # Return to summary page and dismiss popups
            if href:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [NAV] {patient_id} | Returned to summary page: {href}")
                driver.get(href)
                _wait_for_data_load(driver, timeout=30)
                try:
                    dismissed = _dismiss_any_popups(driver)
                    if dismissed:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [NAV] {patient_id} | Dismissed {dismissed} popup/modal(s) on summary load.")
                except Exception as e:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] {patient_id} | Popup dismiss error: {e}")

            # Intake JSON summary extraction
            if staging_dir and patient_id:
                intake_json = staging_dir / f"{patient_id}-intake-details.json"
                if not intake_json.exists():
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [SUMMARY] {patient_id} | Intake JSON does not exist: {intake_json}")
                else:
                    # Family History
                    try:
                        fam_text = _build_family_history_summary(intake_json)
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [SUMMARY] {patient_id} | Family History summary: {fam_text}")
                        fam_filled = False
                        if fam_text:
                            fam_filled = _populate_family_history(driver, fam_text)
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [UI] {patient_id} | Family History UI action: {'Success' if fam_filled else 'Failure'}")
                    except Exception as e:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] {patient_id} | Family History: {e}")
                    # Social History
                    try:
                        soc_text = _build_social_history_summary(intake_json)
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [SUMMARY] {patient_id} | Social History summary: {soc_text}")
                        soc_filled = False
                        if soc_text:
                            soc_filled = _populate_social_history(driver, soc_text)
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [UI] {patient_id} | Social History UI action: {'Success' if soc_filled else 'Failure'}")
                    except Exception as e:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] {patient_id} | Social History: {e}")
                    # Ongoing Medical Problems
                    try:
                        ongoing_text = _build_ongoing_medical_problems_summary(intake_json)
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [SUMMARY] {patient_id} | Ongoing Medical Problems summary: {ongoing_text}")
                        ongoing_filled = False
                        if ongoing_text:
                            ongoing_filled = _populate_ongoing_medical_problems(driver, ongoing_text)
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [UI] {patient_id} | Ongoing Medical Problems UI action: {'Success' if ongoing_filled else 'Failure'}")
                    except Exception as e:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] {patient_id} | Ongoing Medical Problems: {e}")
                    # Major Events
                    try:
                        major_text = _build_major_events_summary(intake_json)
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [SUMMARY] {patient_id} | Major Events summary: {major_text}")
                        major_filled = False
                        if major_text:
                            major_filled = _populate_major_events(driver, major_text)
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [UI] {patient_id} | Major Events UI action: {'Success' if major_filled else 'Failure'}")
                    except Exception as e:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] {patient_id} | Major Events: {e}")
                    # Nutrition History
                    try:
                        nutrition_text = _build_nutrition_history_summary(intake_json)
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [SUMMARY] {patient_id} | Nutrition History summary: {nutrition_text}")
                        nutrition_filled = False
                        if nutrition_text:
                            nutrition_filled = _populate_nutrition_history(driver, nutrition_text)
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [UI] {patient_id} | Nutrition History UI action: {'Success' if nutrition_filled else 'Failure'}")
                    except Exception as e:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] {patient_id} | Nutrition History: {e}")

                    # Preventive Care (Female only)
                    try:
                        from automation.navigation import set_global_gender_flag, process_preventive_care_if_female
                        set_global_gender_flag(intake_json)
                        process_preventive_care_if_female(driver, intake_json, timeout=15)
                    except Exception as e:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] {patient_id} | Preventive Care: {e}")

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [END] End patient loop idx={idx}, patient_id={patient_id}")

            # Move all files for this patient from staging to processed using patient id wildcard
            import shutil
            if staging_dir and patient_id:
                processed_dir = staging_dir.parent / "processed"
                processed_dir.mkdir(exist_ok=True)
                for file in staging_dir.glob(f"{patient_id}*"):
                    if file.is_file():
                        shutil.move(str(file), str(processed_dir / file.name))


# --- Facility (Hormone Center) helpers ---
def _open_facility_dropdown(driver: WebDriver, timeout: int = 10) -> bool:
    """Open the scheduler toolbar's facility dropdown with multiple strategies and verify it opened.

    Success criteria:
      - Visible options found, or
      - The trigger element reports aria-expanded=true, or
      - The container has an 'open' class (e.g., composable-select--open, is-open)
    """
    try:
        from automation.ui_selectors import UI_SELECTORS
        sel = UI_SELECTORS.get("facility_select", {})
        btn_css = sel.get("button")
        container_css = sel.get("container")
        selection_text_css = sel.get("selection_text")
        if not btn_css:
            return False

        # Helper to validate menu visibility by checking for any displayed option
        def _options_visible(short_wait: int = 2) -> bool:
            try:
                # Use a short poll for options to appear
                end = time.time() + short_wait
                while time.time() < end:
                    opts = _list_facility_options(driver, timeout=1)
                    if opts:
                        return True
                return False
            except Exception:
                return False

        def _is_open_state(btn_el: WebElement | None, container_el: WebElement | None) -> bool:
            try:
                if btn_el is not None:
                    expanded = (btn_el.get_attribute("aria-expanded") or "").lower()
                    if expanded == "true":
                        return True
            except Exception:
                pass
            try:
                if container_el is not None:
                    cls = (container_el.get_attribute("class") or "").lower()
                    if any(tok in cls for tok in ("is-open", "open", "composable-select--open")):
                        return True
            except Exception:
                pass
            return False

        # Locate container and candidate trigger elements
        cont = None
        try:
            if container_css:
                cont = WebDriverWait(driver, min(timeout, 4)).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, container_css))
                )
        except Exception:
            cont = None
        # Build a set of trigger candidates (primary first, then fallbacks inside container)
        trigger_candidates: list[WebElement] = []
        btn = None
        try:
            btn = WebDriverWait(driver, min(timeout, 4)).until(EC.presence_of_element_located((By.CSS_SELECTOR, btn_css)))
            trigger_candidates.append(btn)
        except Exception:
            btn = None
        # Fallbacks commonly used by composable/select UIs
        fallback_selectors = [
            ".composable-select__control",
            "[role='combobox']",
            ".composable-select",
            "[data-element='dropdown-trigger']",
        ]
        for css in fallback_selectors:
            try:
                scope = cont if cont is not None else driver
                els = scope.find_elements(By.CSS_SELECTOR, css)
                for e in els:
                    if e not in trigger_candidates:
                        trigger_candidates.append(e)
            except Exception:
                continue
        # Ensure we have at least the container itself as last resort
        if cont is not None and cont not in trigger_candidates:
            trigger_candidates.append(cont)

        # Scroll first candidate into view
        if trigger_candidates:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", trigger_candidates[0])
            except Exception:
                pass

        # Attempt 1: regular click on first candidate
        try:
            if btn is not None:
                WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, btn_css)))
        except Exception:
            pass
        try:
            (btn or trigger_candidates[0]).click()
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", (btn or trigger_candidates[0]))
            except Exception:
                pass
        if _options_visible(2) or _is_open_state(btn, cont):
            LOGGER.info("Facilities dropdown opened via click.")
            return True

        # Attempt 2: focus + SPACE
        try:
            (btn or trigger_candidates[0]).send_keys(Keys.SPACE)
        except Exception:
            pass
        if _options_visible(1) or _is_open_state(btn, cont):
            LOGGER.info("Facilities dropdown opened via SPACE on button.")
            return True

        # Attempt 3: focus + ENTER
        try:
            (btn or trigger_candidates[0]).send_keys(Keys.ENTER)
        except Exception:
            pass
        if _options_visible(1) or _is_open_state(btn, cont):
            LOGGER.info("Facilities dropdown opened via ENTER on button.")
            return True

        # Attempt 3b: ARROW_DOWN often opens listboxes
        try:
            (btn or trigger_candidates[0]).send_keys(Keys.ARROW_DOWN)
        except Exception:
            pass
        if _options_visible(1) or _is_open_state(btn, cont):
            LOGGER.info("Facilities dropdown opened via ARROW_DOWN on button.")
            return True

        # Attempt 4: click selection text element
        if selection_text_css:
            try:
                sel_el = driver.find_element(By.CSS_SELECTOR, selection_text_css)
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sel_el)
                except Exception:
                    pass
                try:
                    sel_el.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", sel_el)
                if _options_visible(1) or _is_open_state(btn, cont):
                    LOGGER.info("Facilities dropdown opened via selection text click.")
                    return True
            except Exception:
                pass

        # Attempt 5: iterate other trigger candidates and try clicking each
        for cand in trigger_candidates[1:]:
            try:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cand)
                except Exception:
                    pass
                try:
                    cand.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", cand)
                if _options_visible(1) or _is_open_state(btn, cont):
                    LOGGER.info("Facilities dropdown opened via fallback trigger.")
                    return True
            except Exception:
                continue

        # Dump minimal element diagnostics to aid selector fixes
        try:
            btn_html = (btn.get_attribute("outerHTML") or "")[:1000]
        except Exception:
            btn_html = "(error)"
        try:
            cont_html = (cont.get_attribute("outerHTML") or "")[:1000] if cont else "(none)"
        except Exception:
            cont_html = "(error)"
        try:
            btn_expanded = (btn.get_attribute("aria-expanded") if btn else None)
        except Exception:
            btn_expanded = None
        try:
            cont_class = (cont.get_attribute("class") if cont else None)
        except Exception:
            cont_class = None
        LOGGER.info(
            "Facilities dropdown did not open. candidates=%s | btn aria-expanded=%s | container class=%s",
            len(trigger_candidates), btn_expanded, cont_class,
        )
        LOGGER.debug("Facilities btn HTML: %s", btn_html)
        LOGGER.debug("Facilities container HTML: %s", cont_html)
        LOGGER.debug("Facilities dropdown did not open with available strategies.")
        return False
    except Exception:
        LOGGER.debug("Failed to open facility dropdown.", exc_info=True)
        return False


def _list_facility_options(driver: WebDriver, timeout: int = 10) -> list[WebElement]:
    """Return visible option elements for the open facility dropdown.

    This is tolerant of portals: it scans the whole DOM for option-like elements
    and doesn't strictly require a visible listbox container first.
    """
    opts: list[WebElement] = []
    try:
        from automation.ui_selectors import UI_SELECTORS
        selectors = UI_SELECTORS.get("facility_select", {})
        listbox_css = selectors.get("listbox", "[role='listbox']")
        options_css = selectors.get("options", "[role='option'], .composable-select__option")

        # First try: directly scan for option elements (handles body-level portals)
        try:
            candidates = driver.find_elements(By.CSS_SELECTOR, options_css)
            for el in candidates:
                try:
                    if el.is_displayed():
                        opts.append(el)
                except Exception:
                    continue
        except Exception:
            pass

        # If none found, wait briefly for a listbox and try again
        if not opts:
            try:
                WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, listbox_css))
                )
                candidates = driver.find_elements(By.CSS_SELECTOR, options_css)
                for el in candidates:
                    try:
                        if el.is_displayed():
                            opts.append(el)
                    except Exception:
                        continue
            except Exception:
                pass
    except Exception:
        LOGGER.debug("No facility options found (dropdown may not have opened).", exc_info=True)
    return opts


def _get_current_facility_text(driver: WebDriver) -> str:
    try:
        from automation.ui_selectors import UI_SELECTORS
        sel_css = UI_SELECTORS.get("facility_select", {}).get("selection_text")
        if not sel_css:
            return ""
        el = driver.find_element(By.CSS_SELECTOR, sel_css)
        return (el.text or "").strip()
    except Exception:
        return ""


def _select_facility_by_text(driver: WebDriver, label_text: str, timeout: int = 10) -> bool:
    """Open facility dropdown and select the option that matches the label text (case-insensitive contains).

    Returns True on selection success. Logs available options when selection fails.
    """
    target_text_norm = (label_text or "").strip().lower()
    if not target_text_norm:
        return False

    # Try opening quickly up to three times with short timeouts for responsiveness
    for attempt in range(1, 4):
        open_timeout = 3 if attempt == 1 else (4 if attempt == 2 else min(timeout, 6))
        ok = _open_facility_dropdown(driver, timeout=open_timeout)
        if not ok:
            LOGGER.info("Facilities dropdown open failed (attempt %s).", attempt)
            continue
        options = _list_facility_options(driver, timeout=timeout)
        if not options:
            LOGGER.info("No facility options visible after opening (attempt %s).", attempt)
            continue

        # Prefer exact match first, then contains
        target = None
        target_text_lower = target_text_norm
        normalized = []
        for el in options:
            try:
                t = (el.text or "").strip()
                normalized.append(t)
                if t.lower() == target_text_lower:
                    target = el
                    break
            except Exception:
                continue
        if not target:
            for el in options:
                try:
                    t = (el.text or "").strip()
                    if target_text_norm in t.lower():
                        target = el
                        break
                except Exception:
                    continue
        if not target:
            LOGGER.info("Facility option not found for query='%s'. Available: %s", label_text, normalized)
            # Try closing by ESC before next attempt
            try:
                driver.switch_to.active_element.send_keys(Keys.ESCAPE)
            except Exception:
                pass
            continue

        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
        except Exception:
            pass
        try:
            target.click()
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", target)
            except Exception:
                LOGGER.info("Failed to click facility option '%s'.", label_text)
                return False
        # Confirm selection updated (prefer exact equality first)
        try:
            WebDriverWait(driver, 4).until(
                lambda d: (
                    (_get_current_facility_text(d) or "").strip().lower() == target_text_lower
                    or target_text_norm in (_get_current_facility_text(d) or "").strip().lower()
                )
            )
            return True
        except Exception:
            # Log current selection text and available options for diagnostics
            try:
                current_text = _get_current_facility_text(driver)
            except Exception:
                current_text = ""
            LOGGER.info("Facility select did not reflect '%s'. Current='%s'", label_text, current_text)
            return False
    return False


def _get_available_hormone_centers(driver: WebDriver, timeout: int = 10, keyword: str = "hormone center") -> list[str]:
    """Return list of visible facility option texts containing the keyword (default: 'hormone center')."""
    centers: list[str] = []
    if not _open_facility_dropdown(driver, timeout=timeout):
        return centers
    opts = _list_facility_options(driver, timeout=timeout)
    seen = set()
    for el in opts:
        try:
            t = (el.text or "").strip()
            if t and keyword.lower() in t.lower():
                if t not in seen:
                    centers.append(t)
                    seen.add(t)
        except Exception:
            continue
    # Attempt to close dropdown by ESC if needed
    try:
        driver.switch_to.active_element.send_keys(Keys.ESCAPE)
    except Exception:
        pass
    return centers


def run_for_each_hormone_center(driver: WebDriver, date_offset_days: int = -1, staging_dir: Optional[Path] = None) -> None:
    """Iterate each Hormone Center from the scheduler facilities dropdown and process patients for each.

    Steps per center:
      - Ensure we're on Schedule
      - Select the center from dropdown
      - Wait for data load
      - Run the usual navigate_after_login flow (skipping the extra schedule click)
    """
    # We'll navigate to Schedule per center iteration to ensure toolbar present
    # Ensure Schedule once upfront so the toolbar is present for the first selection
    click_schedule(driver)
    centers = _get_available_hormone_centers(driver, timeout=12, keyword="hormone center")
    if not centers:
        LOGGER.info("No Hormone Center options found in facilities dropdown.")
        return
    LOGGER.info("Found %s hormone center(s): %s", len(centers), centers)
    # Step 2: Change the date as required (once for the entire run)
    select_relative_date_in_datepicker(driver, offset_days=date_offset_days)
    for idx, label in enumerate(centers, start=1):
        try:
            # Ensure Schedule between centers (skip for first to avoid double navigation)
            if idx > 1:
                click_schedule(driver)
            ok = _select_facility_by_text(driver, label, timeout=10)
            LOGGER.info("Select center [%s/%s]: '%s' -> %s", idx, len(centers), label, "ok" if ok else "fail")
            if not ok:
                continue
            _wait_for_data_load(driver, timeout=20)
            # Step 4: Click on Appointments
            click_appointments_tab(driver)
            # Step 5: Process patients; skip tabs/date inside processing
            navigate_after_login(
                driver,
                date_offset_days=0,
                staging_dir=staging_dir,
                skip_click_schedule=True,
                skip_tabs_and_date=True,
            )
        except Exception:
            LOGGER.debug("Error while processing center '%s'", label, exc_info=True)


def run_for_named_hormone_centers(
    driver: WebDriver,
    center_names: list[str],
    date_offset_days: int = -1,
    staging_dir: Optional[Path] = None,
) -> None:
    """Select and process one or more specific Hormone Center names.

    Uses case-insensitive substring match per name. If a name isn't selectable, it logs and moves on.
    """
    if not center_names:
        LOGGER.info("No center names provided; nothing to do.")
        return
    # Ensure Schedule once upfront so the toolbar is present for the first selection
    click_schedule(driver)
    # Step 2: Change the date as required (once for the entire run)
    select_relative_date_in_datepicker(driver, offset_days=date_offset_days)

    for idx, name in enumerate(center_names, start=1):
        try:
            if not name or not str(name).strip():
                continue
            label = str(name).strip()
            # Ensure toolbar is present between selections (skip first)
            if idx > 1:
                click_schedule(driver)
            ok = _select_facility_by_text(driver, label, timeout=12)
            LOGGER.info("Select requested center [%s/%s]: '%s' -> %s", idx, len(center_names), label, "ok" if ok else "fail")
            if not ok:
                # Optionally, list available centers for debugging
                avail = _get_available_hormone_centers(driver, timeout=8, keyword="")
                LOGGER.info("Available facilities at failure: %s", avail)
                continue
            _wait_for_data_load(driver, timeout=20)
            # Step 4: Click on Appointments
            click_appointments_tab(driver)
            # Step 5: Process patients; skip tabs/date inside processing
            navigate_after_login(
                driver,
                date_offset_days=0,
                staging_dir=staging_dir,
                skip_click_schedule=True,
                skip_tabs_and_date=True,
            )
        except Exception:
            LOGGER.debug("Error while processing requested center '%s'", name, exc_info=True)

# --- Move generic handler and wrappers to top-level scope ---
def populate_section_generic(driver, summary_text, section_key, timeout=15, debug_capture=None) -> bool:
    """
    Generic handler to populate a summary into a UI section using selectors from UI_SELECTORS.
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
    LOGGER = logging.getLogger(__name__)
    selectors = UI_SELECTORS.get(section_key)
    if not selectors:
        LOGGER.error(f"No selectors found for section '{section_key}'")
        return False
    selectors = UI_SELECTORS.get(section_key)
    if not selectors:
        print(f"[GENERIC] No selectors found for section '{section_key}'")
        return False
    if not summary_text.strip():
        print(f"[GENERIC] {section_key}: Skipped, summary is empty.")
        return False
    wait = WebDriverWait(driver, timeout + 10)
    _dismiss_any_popups(driver)
    # --- Robust section/add/edit button search ---
    section_elems = driver.find_elements(By.CSS_SELECTOR, selectors["section_container"])
    print(f"[GENERIC] {section_key}: Found {len(section_elems)} section containers.")
    found_btn = None
    for idx, section_container in enumerate(section_elems):
        add_btns = section_container.find_elements(By.CSS_SELECTOR, selectors["add_button"])
        print(f"[GENERIC] {section_key}: Section {idx}: Found {len(add_btns)} add buttons.")
        for btn_idx, btn in enumerate(add_btns):
            visible = btn.is_displayed()
            enabled = btn.is_enabled()
            print(f"[GENERIC] {section_key}: Section {idx} Add Button {btn_idx}: visible={visible}, enabled={enabled}")
            if visible and enabled:
                found_btn = btn
                break
        if found_btn:
            section_found_idx = idx
            break
    if not found_btn:
        # Try edit buttons as fallback
        for idx, section_container in enumerate(section_elems):
            edit_btns = section_container.find_elements(By.CSS_SELECTOR, selectors["edit_button"])
            print(f"[GENERIC] {section_key}: Section {idx}: Found {len(edit_btns)} edit buttons.")
            for btn_idx, btn in enumerate(edit_btns):
                visible = btn.is_displayed()
                enabled = btn.is_enabled()
                # --- Diagnostics for edit button ---
                attrs = {
                    "class": btn.get_attribute("class"),
                    "style": btn.get_attribute("style"),
                    "aria": btn.get_attribute("aria-*"),
                    "location": btn.location,
                    "size": btn.size
                }
                print(f"[GENERIC] {section_key}: Section {idx} Edit Button {btn_idx}: visible={visible}, enabled={enabled}, attrs={attrs}")
                # Try to scroll into view if not visible
                if not visible:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        print(f"[GENERIC] {section_key}: Section {idx} Edit Button {btn_idx}: scrolled into view.")
                        visible = btn.is_displayed()
                        print(f"[GENERIC] {section_key}: Section {idx} Edit Button {btn_idx}: visible after scroll={visible}")
                    except Exception as e:
                        print(f"[GENERIC] {section_key}: Section {idx} Edit Button {btn_idx}: scroll error: {e}")
                if visible and enabled:
                    found_btn = btn
                    break
                # Fallback: if enabled but not visible, try JS click
                if enabled and not visible:
                    try:
                        print(f"[GENERIC] {section_key}: Section {idx} Edit Button {btn_idx}: enabled but not visible, trying JS click.")
                        driver.execute_script("arguments[0].click();", btn)
                        found_btn = btn
                        print(f"[GENERIC] {section_key}: Section {idx} Edit Button {btn_idx}: JS click attempted.")
                        break
                    except Exception as e:
                        print(f"[GENERIC] {section_key}: Section {idx} Edit Button {btn_idx}: JS click error: {e}")
            if found_btn:
                section_found_idx = idx
                break
    if not found_btn:
        print(f"[GENERIC] {section_key}: Could not find any visible/enabled add or edit button in any section. Capturing debug artifacts.")
        if debug_capture:
            debug_capture(driver, f"{section_key}-no-add-or-edit-btn")
        return False
    try:
        found_btn.click()
    except Exception:
        try:
            print(f"[GENERIC] {section_key}: Could not click button, trying JS click.")
            driver.execute_script("arguments[0].click();", found_btn)
        except Exception:
            print(f"[GENERIC] {section_key}: Could not click button. Skipping population.")
            if debug_capture:
                debug_capture(driver, f"{section_key}-click-fail")
            return False
    # --- Textarea logic ---
    textarea = None
    if "textarea_candidates" in selectors:
        for css_sel in selectors["textarea_candidates"]:
            try:
                print(f"[GENERIC] {section_key}: Searching for textarea candidate: {css_sel}")
                textarea = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_sel)))
                print(f"[GENERIC] {section_key}: Textarea found: {css_sel}")
                if textarea:
                    break
            except Exception:
                print(f"[GENERIC] {section_key}: Textarea candidate not found: {css_sel}")
                continue
    else:
        try:
            print(f"[GENERIC] {section_key}: Searching for textarea: {selectors['textarea']}")
            textarea = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selectors["textarea"])))
            print(f"[GENERIC] {section_key}: Textarea found: {selectors['textarea']}")
        except Exception:
            print(f"[GENERIC] {section_key}: Textarea not found. Skipping population.")
            if debug_capture:
                debug_capture(driver, f"{section_key}-no-textarea")
            return False
    if not textarea:
        print(f"[GENERIC] {section_key}: Textarea not found. Skipping population.")
        if debug_capture:
            debug_capture(driver, f"{section_key}-no-textarea")
        return False
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
    except Exception as e:
        print(f"[GENERIC] {section_key}: Failed to fill textarea: {e}")
        if debug_capture:
            debug_capture(driver, f"{section_key}-sendkeys-fail")
        return False
    # --- Save button logic ---
    _dismiss_any_popups(driver)
    try:
        print(f"[GENERIC] {section_key}: Searching for save button: {selectors['save_button']}")
        save_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selectors["save_button"])))
        print(f"[GENERIC] {section_key}: Save button found: {selectors['save_button']}")
        save_btn.click()
    except Exception as e:
        print(f"[GENERIC] {section_key}: Save button not found: {e}")
        if debug_capture:
            debug_capture(driver, f"{section_key}-no-save-btn")
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
    print(f"[GENERIC] Summary population complete for section '{section_key}'.")
    return True

def _populate_social_history(driver, summary_text, timeout=15) -> bool:
    return populate_section_generic(driver, summary_text, "social_history", timeout)
    return populate_section_generic(driver, summary_text, "social_history", timeout)
    return populate_section_generic(driver, summary_text, "social_history", timeout)

def _populate_ongoing_medical_problems(driver, summary_text, timeout=15) -> bool:
    return populate_section_generic(driver, summary_text, "ongoing_medical_problems", timeout)

def _populate_major_events(driver, summary_text, timeout=15) -> bool:
    return populate_section_generic(driver, summary_text, "major_events", timeout)
    return populate_section_generic(driver, summary_text, "ongoing_medical_problems", timeout)
    # TODO: Implement family history summary builder
    return ""
    # TODO: Implement social history summary builder
    return ""
    # TODO: Implement major events summary builder
    return ""
    # TODO: Implement ongoing medical problems summary builder
    return ""
    return populate_section_generic(driver, summary_text, "major_events", timeout)
    return populate_section_generic(driver, summary_text, "ongoing_medical_problems", timeout)
    # TODO: Implement family history summary builder
    return ""
    # TODO: Implement social history summary builder
    return ""
    # TODO: Implement major events summary builder
    return ""
    # TODO: Implement ongoing medical problems summary builder
    return ""
    return populate_section_generic(driver, summary_text, "major_events", timeout)

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
        pass
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
    # Clean Downloads of old intake*.pdf files (case insensitive) before triggering a new download
    downloads_dir = _get_downloads_dir()
    try:
        for p in downloads_dir.glob("*.pdf"):
            if "intake" in p.name.lower():
                try:
                    p.unlink(missing_ok=True)
                except Exception:
                    continue
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
        pdfs = [p for p in downloads_dir.glob("*.pdf")
                if "intake" in p.name.lower() and not p.name.endswith(".crdownload")]
        if pdfs:
            # Select the most recently modified file
            latest_pdf = max(pdfs, key=lambda p: p.stat().st_mtime)
            crdl = latest_pdf.with_suffix(latest_pdf.suffix + ".crdownload")
            if not crdl.exists():
                return latest_pdf
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
    # Actual popup dismiss logic should go here
    # For now, just return 0 (no popups dismissed)
    dismissed = 0
    return dismissed
    return True


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

