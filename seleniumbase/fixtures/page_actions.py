"""This module contains useful methods for waiting on elements to load.

These methods improve and expand on existing WebDriver commands.
Improvements include making WebDriver commands more robust and more reliable
by giving page elements enough time to load before taking action on them.

The default option for searching for elements is by "css selector".
This can be changed by overriding the "By" parameter from this import:
> from selenium.webdriver.common.by import By
Options are:
By.CSS_SELECTOR        # "css selector"
By.CLASS_NAME          # "class name"
By.ID                  # "id"
By.NAME                # "name"
By.LINK_TEXT           # "link text"
By.XPATH               # "xpath"
By.TAG_NAME            # "tag name"
By.PARTIAL_LINK_TEXT   # "partial link text"
"""
import codecs
import fasteners
import os
import time
from contextlib import suppress
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import ElementNotVisibleException
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import NoSuchAttributeException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoSuchWindowException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from seleniumbase.common.exceptions import LinkTextNotFoundException
from seleniumbase.common.exceptions import TextNotVisibleException
from seleniumbase.config import settings
from seleniumbase.fixtures import constants
from seleniumbase.fixtures import page_utils
from seleniumbase.fixtures import shared_utils


def is_element_present(driver, selector, by="css selector"):
    """
    Returns whether the specified element selector is present on the page.
    @Params
    driver - the webdriver object (required)
    selector - the locator for identifying the page element (required)
    by - the type of selector being used (Default: "css selector")
    @Returns
    Boolean (is element present)
    """
    if __is_cdp_swap_needed(driver):
        return driver.cdp.is_element_present(selector)
    selector, by = page_utils.swap_selector_and_by_if_reversed(selector, by)
    try:
        driver.find_element(by=by, value=selector)
        return True
    except Exception:
        return False


def is_element_visible(driver, selector, by="css selector"):
    """
    Returns whether the specified element selector is visible on the page.
    @Params
    driver - the webdriver object (required)
    selector - the locator for identifying the page element (required)
    by - the type of selector being used (Default: "css selector")
    @Returns
    Boolean (is element visible)
    """
    if __is_cdp_swap_needed(driver):
        return driver.cdp.is_element_visible(selector)
    selector, by = page_utils.swap_selector_and_by_if_reversed(selector, by)
    try:
        element = driver.find_element(by=by, value=selector)
        return element.is_displayed()
    except Exception:
        return False


def is_element_clickable(driver, selector, by="css selector"):
    """
    Returns whether the specified element selector is clickable.
    @Params
    driver - the webdriver object (required)
    selector - the locator for identifying the page element (required)
    by - the type of selector being used (Default: "css selector")
    @Returns
    Boolean (is element clickable)
    """
    _reconnect_if_disconnected(driver)
    try:
        element = driver.find_element(by=by, value=selector)
        if element.is_displayed() and element.is_enabled():
            return True
        return False
    except Exception:
        return False


def is_element_enabled(driver, selector, by="css selector"):
    """
    Returns whether the specified element selector is enabled on the page.
    @Params
    driver - the webdriver object (required)
    selector - the locator for identifying the page element (required)
    by - the type of selector being used (Default: "css selector")
    @Returns
    Boolean (is element enabled)
    """
    _reconnect_if_disconnected(driver)
    try:
        element = driver.find_element(by=by, value=selector)
        return element.is_enabled()
    except Exception:
        return False


def is_text_visible(driver, text, selector="html", by="css selector"):
    """
    Returns whether the text substring is visible in the given selector.
    @Params
    driver - the webdriver object (required)
    text - the text string to search for (required)
    selector - the locator for identifying the page element
    by - the type of selector being used (Default: "css selector")
    @Returns
    Boolean (is text visible)
    """
    _reconnect_if_disconnected(driver)
    selector, by = page_utils.swap_selector_and_by_if_reversed(selector, by)
    text = str(text)
    try:
        element = driver.find_element(by=by, value=selector)
        element_text = element.text
        if shared_utils.is_safari(driver):
            if element.tag_name.lower() in ["input", "textarea"]:
                element_text = element.get_attribute("value")
            else:
                element_text = element.get_attribute("innerText")
        elif element.tag_name.lower() in ["input", "textarea"]:
            element_text = element.get_property("value")
        return element.is_displayed() and text in element_text
    except Exception:
        return False


def is_exact_text_visible(driver, text, selector, by="css selector"):
    """
    Returns whether the exact text is visible in the given selector.
    (Ignores leading and trailing whitespace)
    @Params
    driver - the webdriver object (required)
    text - the text string to search for (required)
    selector - the locator for identifying the page element (required)
    by - the type of selector being used (Default: "css selector")
    @Returns
    Boolean (is text visible)
    """
    _reconnect_if_disconnected(driver)
    selector, by = page_utils.swap_selector_and_by_if_reversed(selector, by)
    text = str(text)
    try:
        element = driver.find_element(by=by, value=selector)
        element_text = element.text
        if shared_utils.is_safari(driver):
            if element.tag_name.lower() in ["input", "textarea"]:
                element_text = element.get_attribute("value")
            else:
                element_text = element.get_attribute("innerText")
        elif element.tag_name.lower() in ["input", "textarea"]:
            element_text = element.get_property("value")
        return (
            element.is_displayed()
            and text.strip() == element_text.strip()
        )
    except Exception:
        return False


def is_attribute_present(
    driver, selector, attribute, value=None, by="css selector"
):
    """
    Returns whether the specified attribute is present in the given selector.
    @Params
    driver - the webdriver object (required)
    selector - the locator for identifying the page element (required)
    attribute - the attribute that is expected for the element (required)
    value - the attribute value that is expected (Default: None)
    by - the type of selector being used (Default: "css selector")
    @Returns
    Boolean (is attribute present)
    """
    _reconnect_if_disconnected(driver)
    try:
        element = driver.find_element(by=by, value=selector)
        found_value = element.get_attribute(attribute)
        if found_value is None:
            return False
        if value is not None:
            if found_value == value:
                return True
            else:
                return False
        else:
            return True
    except Exception:
        return False


def is_non_empty_text_visible(driver, selector, by="css selector"):
    """
    Returns whether the element has any text visible for the given selector.
    @Params
    driver - the webdriver object (required)
    selector - the locator for identifying the page element (required)
    by - the type of selector being used (Default: "css selector")
    @Returns
    Boolean (is any text visible in the element with the selector)
    """
    _reconnect_if_disconnected(driver)
    try:
        element = driver.find_element(by=by, value=selector)
        element_text = element.text
        if shared_utils.is_safari(driver):
            if element.tag_name.lower() in ["input", "textarea"]:
                element_text = element.get_attribute("value")
            else:
                element_text = element.get_attribute("innerText")
        elif element.tag_name.lower() in ["input", "textarea"]:
            element_text = element.get_property("value")
        element_text = element_text.strip()
        return element.is_displayed() and len(element_text) > 0
    except Exception:
        return False


def hover_on_element(driver, selector, by="css selector"):
    """
    Fires the hover event for the specified element by the given selector.
    @Params
    driver - the webdriver object (required)
    selector - the locator for identifying the page element (required)
    by - the type of selector being used (Default: "css selector")
    """
    _reconnect_if_disconnected(driver)
    element = driver.find_element(by=by, value=selector)
    hover = ActionChains(driver).move_to_element(element)
    hover.perform()
    return element


def hover_element(driver, element):
    """
    Similar to hover_on_element(), but uses found element, not a selector.
    """
    _reconnect_if_disconnected(driver)
    hover = ActionChains(driver).move_to_element(element)
    hover.perform()
    return element


def timeout_exception(exception, message):
    exc, msg = shared_utils.format_exc(exception, message)
    raise exc(msg)


def hover_and_click(
    driver,
    hover_selector,
    click_selector,
    hover_by="css selector",
    click_by="css selector",
    timeout=settings.SMALL_TIMEOUT,
    js_click=False,
):
    """
    Fires the hover event for a specified element by a given selector, then
    clicks on another element specified. Useful for dropdown hover based menus.
    @Params
    driver - the webdriver object (required)
    hover_selector - the css selector to hover over (required)
    click_selector - the css selector to click on (required)
    hover_by - the hover selector type to search by (Default: "css selector")
    click_by - the click selector type to search by (Default: "css selector")
    timeout - number of seconds to wait for click element to appear after hover
    js_click - the option to use js_click() instead of click() on the last part
    """
    _reconnect_if_disconnected(driver)
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    element = driver.find_element(by=hover_by, value=hover_selector)
    hover = ActionChains(driver).move_to_element(element)
    for x in range(int(timeout * 10)):
        try:
            hover.perform()
            element = driver.find_element(by=click_by, value=click_selector)
            if js_click:
                driver.execute_script("arguments[0].click();", element)
            else:
                element.click()
            return element
        except Exception:
            now_ms = time.time() * 1000.0
            if now_ms >= stop_ms:
                break
            time.sleep(0.1)
    plural = "s"
    if timeout == 1:
        plural = ""
    message = "Element {%s} was not present after %s second%s!" % (
        click_selector,
        timeout,
        plural,
    )
    timeout_exception(NoSuchElementException, message)


def hover_element_and_click(
    driver,
    element,
    click_selector,
    click_by="css selector",
    timeout=settings.SMALL_TIMEOUT,
):
    """
    Similar to hover_and_click(), but assumes top element is already found.
    """
    _reconnect_if_disconnected(driver)
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    hover = ActionChains(driver).move_to_element(element)
    for x in range(int(timeout * 10)):
        try:
            hover.perform()
            element = driver.find_element(by=click_by, value=click_selector)
            element.click()
            return element
        except Exception:
            now_ms = time.time() * 1000.0
            if now_ms >= stop_ms:
                break
            time.sleep(0.1)
    plural = "s"
    if timeout == 1:
        plural = ""
    message = "Element {%s} was not present after %s second%s!" % (
        click_selector,
        timeout,
        plural,
    )
    timeout_exception(NoSuchElementException, message)


def hover_element_and_double_click(
    driver,
    element,
    click_selector,
    click_by="css selector",
    timeout=settings.SMALL_TIMEOUT,
):
    _reconnect_if_disconnected(driver)
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    hover = ActionChains(driver).move_to_element(element)
    for x in range(int(timeout * 10)):
        try:
            hover.perform()
            element_2 = driver.find_element(by=click_by, value=click_selector)
            actions = ActionChains(driver)
            actions.move_to_element(element_2)
            actions.double_click(element_2)
            actions.perform()
            return element_2
        except Exception:
            now_ms = time.time() * 1000.0
            if now_ms >= stop_ms:
                break
            time.sleep(0.1)
    plural = "s"
    if timeout == 1:
        plural = ""
    message = "Element {%s} was not present after %s second%s!" % (
        click_selector,
        timeout,
        plural,
    )
    timeout_exception(NoSuchElementException, message)


def wait_for_element_present(
    driver,
    selector,
    by="css selector",
    timeout=settings.LARGE_TIMEOUT,
    original_selector=None,
    ignore_test_time_limit=False,
):
    """
    Searches for the specified element by the given selector. Returns the
    element object if it exists in the HTML. (The element can be invisible.)
    Raises NoSuchElementException if the element does not exist in the HTML
    within the specified timeout.
    @Params
    driver - the webdriver object
    selector - the locator for identifying the page element (required)
    by - the type of selector being used (Default: "css selector")
    timeout - the time to wait for elements in seconds
    original_selector - handle pre-converted ":contains(TEXT)" selector
    ignore_test_time_limit - ignore test time limit (NOT related to timeout)
    @Returns
    A web element object
    """
    _reconnect_if_disconnected(driver)
    element = None
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    for x in range(int(timeout * 10)):
        if not ignore_test_time_limit:
            shared_utils.check_if_time_limit_exceeded()
        try:
            element = driver.find_element(by=by, value=selector)
            return element
        except Exception:
            now_ms = time.time() * 1000.0
            if now_ms >= stop_ms:
                break
            time.sleep(0.1)
    plural = "s"
    if timeout == 1:
        plural = ""
    if not element:
        if (
            original_selector
            and ":contains(" in original_selector
            and "contains(." in selector
        ):
            selector = original_selector
        message = "Element {%s} was not present after %s second%s!" % (
            selector,
            timeout,
            plural,
        )
        timeout_exception(NoSuchElementException, message)
    else:
        return element


def wait_for_element_visible(
    driver,
    selector,
    by="css selector",
    timeout=settings.LARGE_TIMEOUT,
    original_selector=None,
    ignore_test_time_limit=False,
):
    """
    Searches for the specified element by the given selector. Returns the
    element object if the element is present and visible on the page.
    Raises NoSuchElementException if the element does not exist in the HTML
    within the specified timeout.
    Raises ElementNotVisibleException if the element exists in the HTML,
    but is not visible (eg. opacity is "0") within the specified timeout.
    @Params
    driver - the webdriver object (required)
    selector - the locator for identifying the page element (required)
    by - the type of selector being used (Default: "css selector")
    timeout - the time to wait for elements in seconds
    original_selector - handle pre-converted ":contains(TEXT)" selector
    ignore_test_time_limit - ignore test time limit (NOT related to timeout)
    @Returns
    A web element object
    """
    _reconnect_if_disconnected(driver)
    element = None
    is_present = False
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    for x in range(int(timeout * 10)):
        if not ignore_test_time_limit:
            shared_utils.check_if_time_limit_exceeded()
        try:
            element = driver.find_element(by=by, value=selector)
            is_present = True
            if element.is_displayed():
                return element
            else:
                element = None
                raise Exception()
        except Exception:
            now_ms = time.time() * 1000.0
            if now_ms >= stop_ms:
                break
            time.sleep(0.1)
    plural = "s"
    if timeout == 1:
        plural = ""
    if not element and by != "link text":
        if (
            original_selector
            and ":contains(" in original_selector
            and "contains(." in selector
        ):
            selector = original_selector
        if not is_present:
            # The element does not exist in the HTML
            message = "Element {%s} was not present after %s second%s!" % (
                selector,
                timeout,
                plural,
            )
            timeout_exception(NoSuchElementException, message)
        # The element exists in the HTML, but is not visible
        message = "Element {%s} was not visible after %s second%s!" % (
            selector,
            timeout,
            plural,
        )
        timeout_exception(ElementNotVisibleException, message)
    elif not element and by == "link text":
        message = "Link text {%s} was not found after %s second%s!" % (
            selector,
            timeout,
            plural,
        )
        timeout_exception(LinkTextNotFoundException, message)
    else:
        return element


def wait_for_text_visible(
    driver,
    text,
    selector,
    by="css selector",
    timeout=settings.LARGE_TIMEOUT,
):
    """
    Searches for the specified element by the given selector. Returns the
    element object if the text is present in the element and visible
    on the page.
    Raises NoSuchElementException if the element does not exist in the HTML
    within the specified timeout.
    Raises ElementNotVisibleException if the element exists in the HTML,
    but the text is not visible within the specified timeout.
    @Params
    driver - the webdriver object (required)
    text - the text that is being searched for in the element (required)
    selector - the locator for identifying the page element (required)
    by - the type of selector being used (Default: "css selector")
    timeout - the time to wait for elements in seconds
    browser - used to handle a special edge case when using Safari
    @Returns
    A web element object that contains the text searched for
    """
    _reconnect_if_disconnected(driver)
    element = None
    is_present = False
    full_text = None
    text = str(text)
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    for x in range(int(timeout * 10)):
        shared_utils.check_if_time_limit_exceeded()
        full_text = None
        try:
            element = driver.find_element(by=by, value=selector)
            is_present = True
            if (
                element.tag_name.lower() in ["input", "textarea"]
                and not shared_utils.is_safari(driver)
            ):
                if (
                    element.is_displayed()
                    and text in element.get_property("value")
                ):
                    return element
                else:
                    if element.is_displayed():
                        full_text = element.get_property("value").strip()
                    element = None
                    raise Exception()
            elif shared_utils.is_safari(driver):
                text_attr = "innerText"
                if element.tag_name.lower() in ["input", "textarea"]:
                    text_attr = "value"
                if (
                    element.is_displayed()
                    and text in element.get_attribute(text_attr)
                ):
                    return element
                else:
                    if element.is_displayed():
                        full_text = element.get_attribute(text_attr)
                        full_text = full_text.strip()
                    element = None
                    raise Exception()
            else:
                if element.is_displayed() and text in element.text:
                    return element
                else:
                    if element.is_displayed():
                        full_text = element.text.strip()
                    element = None
                    raise Exception()
        except Exception:
            now_ms = time.time() * 1000.0
            if now_ms >= stop_ms:
                break
            time.sleep(0.1)
    plural = "s"
    if timeout == 1:
        plural = ""
    if not element:
        if not is_present:
            # The element does not exist in the HTML
            message = "Element {%s} was not present after %s second%s!" % (
                selector,
                timeout,
                plural,
            )
            timeout_exception(NoSuchElementException, message)
        # The element exists in the HTML, but the text is not visible
        message = None
        if not full_text or len(str(full_text.replace("\n", ""))) > 320:
            message = (
                "Expected text substring {%s} for {%s} was not visible "
                "after %s second%s!" % (text, selector, timeout, plural)
            )
        else:
            full_text = full_text.replace("\n", "\\n ")
            message = (
                "Expected text substring {%s} for {%s} was not visible "
                "after %s second%s!\n (Actual string found was {%s})"
                % (text, selector, timeout, plural, full_text)
            )
        timeout_exception(TextNotVisibleException, message)
    else:
        return element


def wait_for_exact_text_visible(
    driver,
    text,
    selector,
    by="css selector",
    timeout=settings.LARGE_TIMEOUT,
):
    """
    Searches for the specified element by the given selector. Returns the
    element object if the text matches exactly with the text in the element,
    and the text is visible.
    Raises NoSuchElementException if the element does not exist in the HTML
    within the specified timeout.
    Raises ElementNotVisibleException if the element exists in the HTML,
    but the exact text is not visible within the specified timeout.
    @Params
    driver - the webdriver object (required)
    text - the exact text that is expected for the element (required)
    selector - the locator for identifying the page element (required)
    by - the type of selector being used (Default: "css selector")
    timeout - the time to wait for elements in seconds
    browser - used to handle a special edge case when using Safari
    @Returns
    A web element object that contains the text searched for
    """
    _reconnect_if_disconnected(driver)
    element = None
    is_present = False
    actual_text = None
    text = str(text)
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    for x in range(int(timeout * 10)):
        shared_utils.check_if_time_limit_exceeded()
        actual_text = None
        try:
            element = driver.find_element(by=by, value=selector)
            is_present = True
            if element.tag_name.lower() in ["input", "textarea"]:
                if (
                    element.is_displayed()
                    and text.strip() == element.get_property("value").strip()
                ):
                    return element
                else:
                    if element.is_displayed():
                        actual_text = element.get_property("value").strip()
                    element = None
                    raise Exception()
            elif shared_utils.is_safari(driver):
                text_attr = "innerText"
                if element.tag_name.lower() in ["input", "textarea"]:
                    text_attr = "value"
                if element.is_displayed() and (
                    text.strip() == element.get_attribute(text_attr).strip()
                ):
                    return element
                else:
                    if element.is_displayed():
                        actual_text = element.get_attribute(text_attr)
                        actual_text = actual_text.strip()
                    element = None
                    raise Exception()
            else:
                if (
                    element.is_displayed()
                    and text.strip() == element.text.strip()
                ):
                    return element
                else:
                    if element.is_displayed():
                        actual_text = element.text.strip()
                    element = None
                    raise Exception()
        except Exception:
            now_ms = time.time() * 1000.0
            if now_ms >= stop_ms:
                break
            time.sleep(0.1)
    plural = "s"
    if timeout == 1:
        plural = ""
    if not element:
        if not is_present:
            # The element does not exist in the HTML
            message = "Element {%s} was not present after %s second%s!" % (
                selector,
                timeout,
                plural,
            )
            timeout_exception(NoSuchElementException, message)
        # The element exists in the HTML, but the exact text is not visible
        message = None
        if not actual_text or len(str(actual_text)) > 120:
            message = (
                "Expected exact text {%s} for {%s} was not visible "
                "after %s second%s!" % (text, selector, timeout, plural)
            )
        else:
            actual_text = actual_text.replace("\n", "\\n")
            message = (
                "Expected exact text {%s} for {%s} was not visible "
                "after %s second%s!\n (Actual text was {%s})"
                % (text, selector, timeout, plural, actual_text)
            )
        timeout_exception(TextNotVisibleException, message)
    else:
        return element


def wait_for_any_of_elements_visible(
    driver,
    selectors,
    timeout=settings.LARGE_TIMEOUT,
    original_selectors=[],
    ignore_test_time_limit=False,
):
    """
    Waits for at least one of the elements in the selector list to be visible.
    Returns the first element that is found.
    Raises NoSuchElementException if none of the elements exist in the HTML
    within the specified timeout.
    Raises ElementNotVisibleException if the element exists in the HTML,
    but is not visible (eg. opacity is "0") within the specified timeout.
    @Params
    driver - the webdriver object (required)
    selectors - the list of selectors for identifying page elements (required)
    timeout - the time to wait for elements in seconds
    original_selectors - handle pre-converted ":contains(TEXT)" selectors
    ignore_test_time_limit - ignore test time limit (NOT related to timeout)
    @Returns
    A web element object
    """
    if not isinstance(selectors, (list, tuple)):
        raise Exception("`selectors` must be a list or tuple!")
    if not selectors:
        raise Exception("`selectors` cannot be an empty list!")
    _reconnect_if_disconnected(driver)
    element = None
    any_present = False
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    for x in range(int(timeout * 10)):
        if not ignore_test_time_limit:
            shared_utils.check_if_time_limit_exceeded()
        try:
            for selector in selectors:
                by = "css selector"
                if page_utils.is_xpath_selector(selector):
                    by = "xpath"
                try:
                    element = driver.find_element(by=by, value=selector)
                    any_present = True
                    if element.is_displayed():
                        return element
                    element = None
                except Exception:
                    pass
            raise Exception("Nothing found yet!")
        except Exception:
            now_ms = time.time() * 1000.0
            if now_ms >= stop_ms:
                break
            time.sleep(0.1)
    plural = "s"
    if timeout == 1:
        plural = ""
    if original_selectors:
        selectors = original_selectors
    if not element:
        if not any_present:
            # None of the elements exist in the HTML
            message = (
                "None of the elements {%s} were present after %s second%s!" % (
                    str(selectors),
                    timeout,
                    plural,
                )
            )
            timeout_exception(NoSuchElementException, message)
        # At least one element exists in the HTML, but none are visible
        message = "None of the elements %s were visible after %s second%s!" % (
            str(selectors),
            timeout,
            plural,
        )
        timeout_exception(ElementNotVisibleException, message)
    else:
        return element


def wait_for_any_of_elements_present(
    driver,
    selectors,
    timeout=settings.LARGE_TIMEOUT,
    original_selectors=[],
    ignore_test_time_limit=False,
):
    """
    Waits for at least one of the elements in the selector list to be present.
    Visibility not required. (Eg. <head> hidden in the HTML)
    Returns the first element that is found.
    Raises NoSuchElementException if none of the elements exist in the HTML
    within the specified timeout.
    @Params
    driver - the webdriver object (required)
    selectors - the list of selectors for identifying page elements (required)
    timeout - the time to wait for elements in seconds
    original_selectors - handle pre-converted ":contains(TEXT)" selectors
    ignore_test_time_limit - ignore test time limit (NOT related to timeout)
    @Returns
    A web element object
    """
    if not isinstance(selectors, (list, tuple)):
        raise Exception("`selectors` must be a list or tuple!")
    if not selectors:
        raise Exception("`selectors` cannot be an empty list!")
    _reconnect_if_disconnected(driver)
    element = None
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    for x in range(int(timeout * 10)):
        if not ignore_test_time_limit:
            shared_utils.check_if_time_limit_exceeded()
        try:
            for selector in selectors:
                by = "css selector"
                if page_utils.is_xpath_selector(selector):
                    by = "xpath"
                try:
                    element = driver.find_element(by=by, value=selector)
                    return element
                except Exception:
                    pass
            raise Exception("Nothing found yet!")
        except Exception:
            now_ms = time.time() * 1000.0
            if now_ms >= stop_ms:
                break
            time.sleep(0.1)
    plural = "s"
    if timeout == 1:
        plural = ""
    if original_selectors:
        selectors = original_selectors
    if not element:
        # None of the elements exist in the HTML
        message = (
            "None of the elements %s were present after %s second%s!" % (
                str(selectors),
                timeout,
                plural,
            )
        )
        timeout_exception(NoSuchElementException, message)
    else:
        return element


def wait_for_attribute(
    driver,
    selector,
    attribute,
    value=None,
    by="css selector",
    timeout=settings.LARGE_TIMEOUT,
):
    """
    Searches for the specified element attribute by the given selector.
    Returns the element object if the expected attribute is present
    and the expected attribute value is present (if specified).
    Raises NoSuchElementException if the element does not exist in the HTML
    within the specified timeout.
    Raises NoSuchAttributeException if the element exists in the HTML,
    but the expected attribute/value is not present within the timeout.
    @Params
    driver - the webdriver object (required)
    selector - the locator for identifying the page element (required)
    attribute - the attribute that is expected for the element (required)
    value - the attribute value that is expected (Default: None)
    by - the type of selector being used (Default: "css selector")
    timeout - the time to wait for the element attribute in seconds
    @Returns
    A web element object that contains the expected attribute/value
    """
    _reconnect_if_disconnected(driver)
    element = None
    element_present = False
    attribute_present = False
    found_value = None
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    for x in range(int(timeout * 10)):
        shared_utils.check_if_time_limit_exceeded()
        try:
            element = driver.find_element(by=by, value=selector)
            element_present = True
            attribute_present = False
            found_value = element.get_attribute(attribute)
            if found_value is not None:
                attribute_present = True
            else:
                element = None
                raise Exception()

            if value is not None:
                if found_value == value:
                    return element
                else:
                    element = None
                    raise Exception()
            else:
                return element
        except Exception:
            now_ms = time.time() * 1000.0
            if now_ms >= stop_ms:
                break
            time.sleep(0.1)
    plural = "s"
    if timeout == 1:
        plural = ""
    if not element:
        if not element_present:
            # The element does not exist in the HTML
            message = "Element {%s} was not present after %s second%s!" % (
                selector,
                timeout,
                plural,
            )
            timeout_exception(NoSuchElementException, message)
        if not attribute_present:
            # The element does not have the attribute
            message = (
                "Expected attribute {%s} of element {%s} was not present "
                "after %s second%s!" % (attribute, selector, timeout, plural)
            )
            timeout_exception(NoSuchAttributeException, message)
        # The element attribute exists, but the expected value does not match
        message = (
            "Expected value {%s} for attribute {%s} of element {%s} was not "
            "present after %s second%s! (The actual value was {%s})"
            % (value, attribute, selector, timeout, plural, found_value)
        )
        timeout_exception(NoSuchAttributeException, message)
    else:
        return element


def wait_for_element_clickable(
    driver,
    selector,
    by="css selector",
    timeout=settings.LARGE_TIMEOUT,
    original_selector=None,
):
    """
    Searches for the specified element by the given selector. Returns the
    element object if the element is present, visible, & clickable on the page.
    Raises NoSuchElementException if the element does not exist in the HTML
    within the specified timeout.
    Raises ElementNotVisibleException if the element exists in the HTML,
    but is not visible (eg. opacity is "0") within the specified timeout.
    Raises ElementNotInteractableException if the element is not clickable.
    @Params
    driver - the webdriver object (required)
    selector - the locator for identifying the page element (required)
    by - the type of selector being used (Default: "css selector")
    timeout - the time to wait for elements in seconds
    original_selector - handle pre-converted ":contains(TEXT)" selector
    @Returns
    A web element object
    """
    _reconnect_if_disconnected(driver)
    element = None
    is_present = False
    is_visible = False
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    for x in range(int(timeout * 10)):
        shared_utils.check_if_time_limit_exceeded()
        try:
            element = driver.find_element(by=by, value=selector)
            is_present = True
            if element.is_displayed():
                is_visible = True
                if element.is_enabled():
                    return element
                else:
                    element = None
                    raise Exception()
            else:
                element = None
                raise Exception()
        except Exception:
            now_ms = time.time() * 1000.0
            if now_ms >= stop_ms:
                break
            time.sleep(0.1)
    plural = "s"
    if timeout == 1:
        plural = ""
    if not element and by != "link text":
        if (
            original_selector
            and ":contains(" in original_selector
            and "contains(." in selector
        ):
            selector = original_selector
        if not is_present:
            # The element does not exist in the HTML
            message = "Element {%s} was not present after %s second%s!" % (
                selector,
                timeout,
                plural,
            )
            timeout_exception(NoSuchElementException, message)
        if not is_visible:
            # The element exists in the HTML, but is not visible
            message = "Element {%s} was not visible after %s second%s!" % (
                selector,
                timeout,
                plural,
            )
            timeout_exception(ElementNotVisibleException, message)
        # The element is visible in the HTML, but is not clickable
        message = "Element {%s} was not clickable after %s second%s!" % (
            selector,
            timeout,
            plural,
        )
        timeout_exception(ElementNotInteractableException, message)
    elif not element and by == "link text" and not is_visible:
        message = "Link text {%s} was not found after %s second%s!" % (
            selector,
            timeout,
            plural,
        )
        timeout_exception(LinkTextNotFoundException, message)
    elif not element and by == "link text" and is_visible:
        message = "Link text {%s} was not clickable after %s second%s!" % (
            selector,
            timeout,
            plural,
        )
        timeout_exception(ElementNotInteractableException, message)
    else:
        return element


def wait_for_element_absent(
    driver,
    selector,
    by="css selector",
    timeout=settings.LARGE_TIMEOUT,
    original_selector=None,
):
    """
    Searches for the specified element by the given selector.
    Raises an exception if the element is still present after the
    specified timeout.
    @Params
    driver - the webdriver object
    selector - the locator for identifying the page element (required)
    by - the type of selector being used (Default: "css selector")
    timeout - the time to wait for elements in seconds
    original_selector - handle pre-converted ":contains(TEXT)" selector
    """
    _reconnect_if_disconnected(driver)
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    for x in range(int(timeout * 10)):
        shared_utils.check_if_time_limit_exceeded()
        try:
            driver.find_element(by=by, value=selector)
            now_ms = time.time() * 1000.0
            if now_ms >= stop_ms:
                break
            time.sleep(0.1)
        except Exception:
            return True
    plural = "s"
    if timeout == 1:
        plural = ""
    if (
        original_selector
        and ":contains(" in original_selector
        and "contains(." in selector
    ):
        selector = original_selector
    message = "Element {%s} was still present after %s second%s!" % (
        selector,
        timeout,
        plural,
    )
    timeout_exception(Exception, message)


def wait_for_element_not_visible(
    driver,
    selector,
    by="css selector",
    timeout=settings.LARGE_TIMEOUT,
    original_selector=None,
):
    """
    Searches for the specified element by the given selector.
    Raises an exception if the element is still visible after the
    specified timeout.
    @Params
    driver - the webdriver object (required)
    selector - the locator for identifying the page element (required)
    by - the type of selector being used (Default: "css selector")
    timeout - the time to wait for the element in seconds
    original_selector - handle pre-converted ":contains(TEXT)" selector
    """
    _reconnect_if_disconnected(driver)
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    for x in range(int(timeout * 10)):
        shared_utils.check_if_time_limit_exceeded()
        try:
            element = driver.find_element(by=by, value=selector)
            if element.is_displayed():
                now_ms = time.time() * 1000.0
                if now_ms >= stop_ms:
                    break
                time.sleep(0.1)
            else:
                return True
        except Exception:
            return True
    plural = "s"
    if timeout == 1:
        plural = ""
    if (
        original_selector
        and ":contains(" in original_selector
        and "contains(." in selector
    ):
        selector = original_selector
    message = "Element {%s} was still visible after %s second%s!" % (
        selector,
        timeout,
        plural,
    )
    timeout_exception(Exception, message)


def wait_for_text_not_visible(
    driver,
    text,
    selector="html",
    by="css selector",
    timeout=settings.LARGE_TIMEOUT,
):
    """
    Searches for the text in the element of the given selector on the page.
    Returns True if the text is not visible on the page within the timeout.
    Raises an exception if the text is still present after the timeout.
    @Params
    driver - the webdriver object (required)
    text - the text that is being searched for in the element (required)
    selector - the locator for identifying the page element (required)
    by - the type of selector being used (Default: "css selector")
    timeout - the time to wait for elements in seconds
    @Returns
    A web element object that contains the text searched for
    """
    _reconnect_if_disconnected(driver)
    text = str(text)
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    for x in range(int(timeout * 10)):
        shared_utils.check_if_time_limit_exceeded()
        if not is_text_visible(driver, text, selector, by=by):
            return True
        now_ms = time.time() * 1000.0
        if now_ms >= stop_ms:
            break
        time.sleep(0.1)
    plural = "s"
    if timeout == 1:
        plural = ""
    message = "Text {%s} in {%s} was still visible after %s second%s!" % (
        text,
        selector,
        timeout,
        plural,
    )
    timeout_exception(Exception, message)


def wait_for_exact_text_not_visible(
    driver,
    text,
    selector="html",
    by="css selector",
    timeout=settings.LARGE_TIMEOUT,
):
    """
    Searches for the text in the element of the given selector on the page.
    Returns True if the element is missing the exact text within the timeout.
    Raises an exception if the exact text is still present after the timeout.
    @Params
    driver - the webdriver object (required)
    text - the text that is being searched for in the element (required)
    selector - the locator for identifying the page element (required)
    by - the type of selector being used (Default: "css selector")
    timeout - the time to wait for elements in seconds
    @Returns
    A web element object that contains the text searched for
    """
    _reconnect_if_disconnected(driver)
    text = str(text)
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    for x in range(int(timeout * 10)):
        shared_utils.check_if_time_limit_exceeded()
        if not is_exact_text_visible(driver, text, selector, by=by):
            return True
        now_ms = time.time() * 1000.0
        if now_ms >= stop_ms:
            break
        time.sleep(0.1)
    plural = "s"
    if timeout == 1:
        plural = ""
    message = (
        "Exact text {%s} for {%s} was still visible after %s second%s!" % (
            text,
            selector,
            timeout,
            plural,
        )
    )
    timeout_exception(Exception, message)


def wait_for_non_empty_text_visible(
    driver, selector, by="css selector", timeout=settings.LARGE_TIMEOUT,
):
    """
    Searches for any text in the element of the given selector.
    Returns the element if it has visible text within the timeout.
    Raises an exception if the element has no text within the timeout.
    Whitespace-only text is considered empty text.
    @Params
    driver - the webdriver object (required)
    text - the text that is being searched for in the element (required)
    selector - the locator for identifying the page element (required)
    by - the type of selector being used (Default: "css selector")
    timeout - the time to wait for elements in seconds
    @Returns
    The web element object that has text
    """
    _reconnect_if_disconnected(driver)
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    element = None
    visible = None
    for x in range(int(timeout * 10)):
        shared_utils.check_if_time_limit_exceeded()
        try:
            element = None
            visible = False
            element = driver.find_element(by=by, value=selector)
            if element.is_displayed():
                visible = True
            element_text = element.text
            if shared_utils.is_safari(driver):
                if element.tag_name.lower() in ["input", "textarea"]:
                    element_text = element.get_attribute("value")
                else:
                    element_text = element.get_attribute("innerText")
            elif element.tag_name.lower() in ["input", "textarea"]:
                element_text = element.get_property("value")
            element_text = element_text.strip()
            if element.is_displayed() and len(element_text) > 0:
                return element
        except Exception:
            element = None
        now_ms = time.time() * 1000.0
        if now_ms >= stop_ms:
            break
        time.sleep(0.1)
    plural = "s"
    if timeout == 1:
        plural = ""
    if not element:
        # The element does not exist in the HTML
        message = "Element {%s} was not present after %s second%s!" % (
            selector,
            timeout,
            plural,
        )
        timeout_exception(NoSuchElementException, message)
    elif not visible:
        # The element exists in the HTML, but is not visible
        message = "Element {%s} was not visible after %s second%s!" % (
            selector,
            timeout,
            plural,
        )
        timeout_exception(ElementNotVisibleException, message)
    else:
        # The element exists in the HTML, but has no visible text
        message = (
            "Element {%s} has no visible text after %s second%s!"
            "" % (selector, timeout, plural)
        )
        timeout_exception(TextNotVisibleException, message)


def wait_for_attribute_not_present(
    driver,
    selector,
    attribute,
    value=None,
    by="css selector",
    timeout=settings.LARGE_TIMEOUT,
):
    """
    Searches for the specified element attribute by the given selector.
    Returns True if the attribute isn't present on the page within the timeout.
    Also returns True if the element is not present within the timeout.
    Raises an exception if the attribute is still present after the timeout.
    @Params
    driver - the webdriver object (required)
    selector - the locator for identifying the page element (required)
    attribute - the element attribute (required)
    value - the attribute value (Default: None)
    by - the type of selector being used (Default: "css selector")
    timeout - the time to wait for the element attribute in seconds
    """
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    for x in range(int(timeout * 10)):
        shared_utils.check_if_time_limit_exceeded()
        if not is_attribute_present(
            driver, selector, attribute, value=value, by=by
        ):
            return True
        now_ms = time.time() * 1000.0
        if now_ms >= stop_ms:
            break
        time.sleep(0.1)
    plural = "s"
    if timeout == 1:
        plural = ""
    message = (
        "Attribute {%s} of element {%s} was still present after %s second%s!"
        "" % (attribute, selector, timeout, plural)
    )
    if value:
        message = (
            "Value {%s} for attribute {%s} of element {%s} was still present "
            "after %s second%s!"
            "" % (value, attribute, selector, timeout, plural)
        )
    timeout_exception(Exception, message)


def find_visible_elements(driver, selector, by="css selector", limit=0):
    """
    Finds all WebElements that match a selector and are visible.
    Similar to webdriver.find_elements().
    If "limit" is set and > 0, will only return that many elements.
    @Params
    driver - the webdriver object (required)
    selector - the locator for identifying the page element (required)
    by - the type of selector being used (Default: "css selector")
    limit - the maximum number of elements to return if > 0.
    """
    _reconnect_if_disconnected(driver)
    elements = driver.find_elements(by=by, value=selector)
    if limit and limit > 0 and len(elements) > limit:
        elements = elements[:limit]
    try:
        v_elems = [element for element in elements if element.is_displayed()]
        return v_elems
    except (StaleElementReferenceException, ElementNotInteractableException):
        time.sleep(0.1)
        elements = driver.find_elements(by=by, value=selector)
        extra_elements = []
        if limit and limit > 0 and len(elements) > limit:
            elements = elements[:limit]
            extra_elements = elements[limit:]
        v_elems = []
        for element in elements:
            if element.is_displayed():
                v_elems.append(element)
        if extra_elements and limit and len(v_elems) < limit:
            for element in extra_elements:
                if element.is_displayed():
                    v_elems.append(element)
                    if len(v_elems) >= limit:
                        break
        return v_elems


def save_screenshot(
    driver, name, folder=None, selector=None, by="css selector"
):
    """
    Saves a screenshot of the current page.
    If no folder is specified, uses the folder where pytest was called.
    The screenshot will include the entire page unless a selector is given.
    If a provided selector is not found, then takes a full-page screenshot.
    If the folder provided doesn't exist, it will get created.
    The screenshot will be in PNG format: (*.png)
    """
    _reconnect_if_disconnected(driver)
    if not name.endswith(".png"):
        name = name + ".png"
    if folder:
        abs_path = os.path.abspath(".")
        file_path = os.path.join(abs_path, folder)
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        screenshot_path = os.path.join(file_path, name)
    else:
        screenshot_path = name
    if selector:
        try:
            element = driver.find_element(by=by, value=selector)
            element_png = element.screenshot_as_png
            with open(screenshot_path, "wb") as file:
                file.write(element_png)
        except Exception:
            if driver:
                driver.get_screenshot_as_file(screenshot_path)
            else:
                pass
    else:
        if driver:
            driver.get_screenshot_as_file(screenshot_path)
        else:
            pass


def save_page_source(driver, name, folder=None):
    """
    Saves the page HTML to the current directory (or given subfolder).
    If the folder specified doesn't exist, it will get created.
    @Params
    name - The file name to save the current page's HTML to.
    folder - The folder to save the file to. (Default = current folder)
    """
    from seleniumbase.core import log_helper

    if not __is_cdp_swap_needed(driver):
        _reconnect_if_disconnected(driver)  # If disconnected without CDP
    if not name.endswith(".html"):
        name = name + ".html"
    if folder:
        abs_path = os.path.abspath(".")
        file_path = os.path.join(abs_path, folder)
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        html_file_path = os.path.join(file_path, name)
    else:
        html_file_path = name
    page_source = None
    if __is_cdp_swap_needed(driver):
        page_source = driver.cdp.get_page_source()
    else:
        page_source = driver.page_source
    html_file = codecs.open(html_file_path, "w+", "utf-8")
    rendered_source = log_helper.get_html_source_with_base_href(
        driver, page_source
    )
    html_file.write(rendered_source)
    html_file.close()


def wait_for_and_accept_alert(driver, timeout=settings.LARGE_TIMEOUT):
    """
    Wait for and accept an alert. Returns the text from the alert.
    @Params
    driver - the webdriver object (required)
    timeout - the time to wait for the alert in seconds
    """
    _reconnect_if_disconnected(driver)
    alert = wait_for_and_switch_to_alert(driver, timeout)
    alert_text = alert.text
    alert.accept()
    return alert_text


def wait_for_and_dismiss_alert(driver, timeout=settings.LARGE_TIMEOUT):
    """
    Wait for and dismiss an alert. Returns the text from the alert.
    @Params
    driver - the webdriver object (required)
    timeout - the time to wait for the alert in seconds
    """
    _reconnect_if_disconnected(driver)
    alert = wait_for_and_switch_to_alert(driver, timeout)
    alert_text = alert.text
    alert.dismiss()
    return alert_text


def wait_for_and_switch_to_alert(driver, timeout=settings.LARGE_TIMEOUT):
    """
    Wait for a browser alert to appear, and switch to it. This should be usable
    as a drop-in replacement for driver.switch_to.alert when the alert box
    may not exist yet.
    @Params
    driver - the webdriver object (required)
    timeout - the time to wait for the alert in seconds
    """
    _reconnect_if_disconnected(driver)
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    for x in range(int(timeout * 10)):
        shared_utils.check_if_time_limit_exceeded()
        try:
            alert = driver.switch_to.alert
            # Raises exception if no alert present
            dummy_variable = alert.text  # noqa
            return alert
        except NoAlertPresentException:
            now_ms = time.time() * 1000.0
            if now_ms >= stop_ms:
                break
            time.sleep(0.1)
    message = "Alert was not present after %s seconds!" % timeout
    timeout_exception(Exception, message)


def switch_to_frame(
    driver, frame, timeout=settings.SMALL_TIMEOUT, invisible=False
):
    """
    Wait for an iframe to appear, and switch to it. This should be
    usable as a drop-in replacement for driver.switch_to.frame().
    @Params
    driver - the webdriver object (required)
    frame - the frame element, name, id, index, or selector
    timeout - the time to wait for the alert in seconds
    invisible - if True, the iframe can be invisible
    """
    _reconnect_if_disconnected(driver)
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    for x in range(int(timeout * 10)):
        shared_utils.check_if_time_limit_exceeded()
        try:
            driver.switch_to.frame(frame)
            return True
        except Exception:
            if isinstance(frame, str):
                by = None
                if page_utils.is_xpath_selector(frame):
                    by = "xpath"
                else:
                    by = "css selector"
                if (
                    is_element_visible(driver, frame, by=by)
                    or (invisible and is_element_present(driver, frame, by=by))
                ):
                    with suppress(Exception):
                        element = driver.find_element(by=by, value=frame)
                        driver.switch_to.frame(element)
                        return True
            now_ms = time.time() * 1000.0
            if now_ms >= stop_ms:
                break
            time.sleep(0.1)
    plural = "s"
    if timeout == 1:
        plural = ""
    presence = "visible"
    if invisible:
        presence = "present"
    message = "Frame {%s} was not %s after %s second%s!" % (
        frame,
        presence,
        timeout,
        plural,
    )
    timeout_exception(Exception, message)


def __switch_to_window(driver, window_handle, uc_lock=True):
    if (
        hasattr(driver, "_is_using_uc")
        and driver._is_using_uc
        and uc_lock
    ):
        gui_lock = fasteners.InterProcessLock(
            constants.MultiBrowser.PYAUTOGUILOCK
        )
        with gui_lock:
            driver.switch_to.window(window_handle)
    else:
        driver.switch_to.window(window_handle)
    return True


def switch_to_window(
    driver,
    window,
    timeout=settings.SMALL_TIMEOUT,
    uc_lock=True,
):
    """
    Wait for a window to appear, and switch to it. This should be usable
    as a drop-in replacement for driver.switch_to.window().
    @Params
    driver - the webdriver object (required)
    window - the window index or window handle
    timeout - the time to wait for the window in seconds
    uc_lock - if UC Mode and True, switch_to_window() uses thread-locking
    """
    _reconnect_if_disconnected(driver)
    if window == -1:
        window = len(driver.window_handles) - 1
    start_ms = time.time() * 1000.0
    stop_ms = start_ms + (timeout * 1000.0)
    if isinstance(window, int):
        if shared_utils.is_safari(driver):
            # Reversed window_handles on Safari
            window = len(driver.window_handles) - 1 - window
            if window < 0:
                window = 0
        for x in range(int(timeout * 10)):
            shared_utils.check_if_time_limit_exceeded()
            try:
                window_handle = driver.window_handles[window]
                __switch_to_window(driver, window_handle, uc_lock=uc_lock)
                return True
            except IndexError:
                now_ms = time.time() * 1000.0
                if now_ms >= stop_ms:
                    break
                time.sleep(0.1)
        plural = "s"
        if timeout == 1:
            plural = ""
        message = "Window {%s} was not present after %s second%s!" % (
            window,
            timeout,
            plural,
        )
        timeout_exception(Exception, message)
    else:
        window_handle = window
        for x in range(int(timeout * 10)):
            shared_utils.check_if_time_limit_exceeded()
            try:
                __switch_to_window(driver, window_handle, uc_lock=uc_lock)
                return True
            except NoSuchWindowException:
                now_ms = time.time() * 1000.0
                if now_ms >= stop_ms:
                    break
                time.sleep(0.1)
        plural = "s"
        if timeout == 1:
            plural = ""
        message = "Window {%s} was not present after %s second%s!" % (
            window,
            timeout,
            plural,
        )
        timeout_exception(Exception, message)


############

# Special methods for use with UC Mode

def _reconnect_if_disconnected(driver):
    if (
        hasattr(driver, "_is_using_uc")
        and driver._is_using_uc
        and hasattr(driver, "is_connected")
        and not driver.is_connected()
    ):
        with suppress(Exception):
            driver.connect()


def __is_cdp_swap_needed(driver):
    """If the driver is disconnected, use a CDP method when available."""
    return shared_utils.is_cdp_swap_needed(driver)


############

# Support methods for direct use from driver

def open_url(driver, url):
    if __is_cdp_swap_needed(driver):
        driver.cdp.open(url)
        return
    url = str(url).strip()  # Remove leading and trailing whitespace
    if not page_utils.looks_like_a_page_url(url):
        if page_utils.is_valid_url("https://" + url):
            url = "https://" + url
    driver.get(url)


def click(driver, selector, by="css selector", timeout=settings.SMALL_TIMEOUT):
    selector, by = page_utils.recalculate_selector(selector, by)
    if __is_cdp_swap_needed(driver):
        driver.cdp.click(selector)
        return
    element = wait_for_element_clickable(
        driver, selector, by=by, timeout=timeout
    )
    element.click()


def click_link(driver, link_text, timeout=settings.SMALL_TIMEOUT):
    if __is_cdp_swap_needed(driver):
        driver.cdp.click_link(link_text)
        return
    element = wait_for_element_clickable(
        driver, link_text, by="link text", timeout=timeout
    )
    element.click()


def click_if_visible(
    driver, selector, by="css selector", timeout=0
):
    selector, by = page_utils.recalculate_selector(selector, by)
    if __is_cdp_swap_needed(driver):
        driver.cdp.click_if_visible(selector)
        return
    if is_element_visible(driver, selector, by=by):
        click(driver, selector, by=by, timeout=1)
    elif timeout > 0:
        with suppress(Exception):
            wait_for_element_visible(
                driver, selector, by=by, timeout=timeout
            )
        if is_element_visible(driver, selector, by=by):
            click(driver, selector, by=by, timeout=1)


def click_active_element(driver):
    if __is_cdp_swap_needed(driver):
        driver.cdp.click_active_element()
        return
    driver.execute_script("document.activeElement.click();")


def js_click(
    driver, selector, by="css selector", timeout=settings.SMALL_TIMEOUT
):
    selector, by = page_utils.recalculate_selector(selector, by)
    if __is_cdp_swap_needed(driver):
        driver.cdp.click(selector)
        return
    element = wait_for_element_present(
        driver, selector, by=by, timeout=timeout
    )
    if not element.is_displayed() or not element.is_enabled():
        time.sleep(0.2)  # If not clickable, wait a bit longer before clicking
        element = wait_for_element_present(driver, selector, by=by, timeout=1)
    script = (
        """var simulateClick = function (elem) {
               var evt = new MouseEvent('click', {
                   bubbles: true,
                   cancelable: true,
                   view: window
               });
               var canceled = !elem.dispatchEvent(evt);
           };
           var someLink = arguments[0];
           simulateClick(someLink);"""
    )
    driver.execute_script(script, element)


def send_keys(
    driver, selector, text, by="css selector", timeout=settings.LARGE_TIMEOUT
):
    selector, by = page_utils.recalculate_selector(selector, by)
    if __is_cdp_swap_needed(driver):
        driver.cdp.send_keys(selector, text)
        return
    element = wait_for_element_present(
        driver, selector, by=by, timeout=timeout
    )
    if not text.endswith("\n"):
        element.send_keys(text)
    else:
        element.send_keys(text[:-1])
        element.submit()


def press_keys(
    driver, selector, text, by="css selector", timeout=settings.LARGE_TIMEOUT
):
    selector, by = page_utils.recalculate_selector(selector, by)
    if __is_cdp_swap_needed(driver):
        driver.cdp.press_keys(selector, text)
        return
    element = wait_for_element_present(
        driver, selector, by=by, timeout=timeout
    )
    if not text.endswith("\n"):
        for key in text:
            element.send_keys(key)
    else:
        for key in text[:-1]:
            element.send_keys(key)
        element.send_keys(Keys.RETURN)


def update_text(
    driver, selector, text, by="css selector", timeout=settings.LARGE_TIMEOUT
):
    selector, by = page_utils.recalculate_selector(selector, by)
    if __is_cdp_swap_needed(driver):
        driver.cdp.type(selector, text)
        return
    element = wait_for_element_clickable(
        driver, selector, by=by, timeout=timeout
    )
    element.clear()
    if not text.endswith("\n"):
        element.send_keys(text)
    else:
        element.send_keys(text[:-1])
        element.submit()


def submit(driver, selector, by="css selector"):
    selector, by = page_utils.recalculate_selector(selector, by)
    if __is_cdp_swap_needed(driver):
        driver.cdp.send_keys(selector, "\r\n")
        return
    element = wait_for_element_clickable(
        driver, selector, by=by, timeout=settings.SMALL_TIMEOUT
    )
    element.submit()


def has_attribute(
    driver, selector, attribute, value=None, by="css selector"
):
    selector, by = page_utils.recalculate_selector(selector, by)
    return is_attribute_present(
        driver, selector, attribute, value=value, by=by
    )


def assert_element_visible(
    driver, selector, by="css selector", timeout=settings.SMALL_TIMEOUT
):
    original_selector = None
    if page_utils.is_valid_by(by):
        original_selector = selector
    elif page_utils.is_valid_by(selector):
        original_selector = by
    selector, by = page_utils.recalculate_selector(selector, by)
    if __is_cdp_swap_needed(driver):
        driver.cdp.assert_element(selector)
        return True
    wait_for_element_visible(
        driver,
        selector,
        by=by,
        timeout=timeout,
        original_selector=original_selector,
    )


def assert_element_present(
    driver, selector, by="css selector", timeout=settings.SMALL_TIMEOUT
):
    original_selector = None
    if page_utils.is_valid_by(by):
        original_selector = selector
    elif page_utils.is_valid_by(selector):
        original_selector = by
    selector, by = page_utils.recalculate_selector(selector, by)
    if __is_cdp_swap_needed(driver):
        driver.cdp.assert_element_present(selector)
        return True
    wait_for_element_present(
        driver,
        selector,
        by=by,
        timeout=timeout,
        original_selector=original_selector,
    )


def assert_element_not_visible(
    driver, selector, by="css selector", timeout=settings.SMALL_TIMEOUT
):
    original_selector = None
    if page_utils.is_valid_by(by):
        original_selector = selector
    elif page_utils.is_valid_by(selector):
        original_selector = by
    selector, by = page_utils.recalculate_selector(selector, by)
    wait_for_element_not_visible(
        driver,
        selector,
        by=by,
        timeout=timeout,
        original_selector=original_selector,
    )


def assert_text(
    driver,
    text,
    selector="html",
    by="css selector",
    timeout=settings.SMALL_TIMEOUT,
):
    selector, by = page_utils.recalculate_selector(selector, by)
    if __is_cdp_swap_needed(driver):
        driver.cdp.assert_text(text, selector)
        return True
    wait_for_text_visible(
        driver, text.strip(), selector, by=by, timeout=timeout
    )


def assert_exact_text(
    driver,
    text,
    selector="html",
    by="css selector",
    timeout=settings.SMALL_TIMEOUT,
):
    selector, by = page_utils.recalculate_selector(selector, by)
    if __is_cdp_swap_needed(driver):
        driver.cdp.assert_exact_text(text, selector)
        return True
    wait_for_exact_text_visible(
        driver, text.strip(), selector, by=by, timeout=timeout
    )


def assert_non_empty_text(
    driver,
    selector,
    by="css selector",
    timeout=settings.SMALL_TIMEOUT,
):
    selector, by = page_utils.recalculate_selector(selector, by)
    wait_for_non_empty_text_visible(
        driver, selector, by=by, timeout=timeout
    )


def assert_text_not_visible(
    driver,
    text,
    selector="html",
    by="css selector",
    timeout=settings.SMALL_TIMEOUT,
):
    selector, by = page_utils.recalculate_selector(selector, by)
    wait_for_text_not_visible(
        driver, text.strip(), selector, by=by, timeout=timeout
    )


def wait_for_element(
    driver,
    selector,
    by="css selector",
    timeout=settings.LARGE_TIMEOUT,
):
    original_selector = None
    if page_utils.is_valid_by(by):
        original_selector = selector
    elif page_utils.is_valid_by(selector):
        original_selector = by
    selector, by = page_utils.recalculate_selector(selector, by)
    if __is_cdp_swap_needed(driver):
        return driver.cdp.select(selector)
    return wait_for_element_visible(
        driver=driver,
        selector=selector,
        by=by,
        timeout=timeout,
        original_selector=original_selector,
    )


def wait_for_selector(
    driver,
    selector,
    by="css selector",
    timeout=settings.LARGE_TIMEOUT,
):
    original_selector = None
    if page_utils.is_valid_by(by):
        original_selector = selector
    elif page_utils.is_valid_by(selector):
        original_selector = by
    selector, by = page_utils.recalculate_selector(selector, by)
    if __is_cdp_swap_needed(driver):
        return driver.cdp.select(selector)
    return wait_for_element_present(
        driver=driver,
        selector=selector,
        by=by,
        timeout=timeout,
        original_selector=original_selector,
    )


def wait_for_text(
    driver,
    text,
    selector,
    by="css selector",
    timeout=settings.LARGE_TIMEOUT,
):
    selector, by = page_utils.recalculate_selector(selector, by)
    if __is_cdp_swap_needed(driver):
        return driver.cdp.find_element(selector)
    return wait_for_text_visible(
        driver=driver,
        text=text,
        selector=selector,
        by=by,
        timeout=timeout,
    )


def wait_for_exact_text(
    driver,
    text,
    selector,
    by="css selector",
    timeout=settings.LARGE_TIMEOUT,
):
    selector, by = page_utils.recalculate_selector(selector, by)
    return wait_for_exact_text_visible(
        driver=driver,
        text=text,
        selector=selector,
        by=by,
        timeout=timeout,
    )


def wait_for_non_empty_text(
    driver,
    selector,
    by="css selector",
    timeout=settings.LARGE_TIMEOUT,
):
    selector, by = page_utils.recalculate_selector(selector, by)
    return wait_for_non_empty_text_visible(
        driver=driver,
        selector=selector,
        by=by,
        timeout=timeout,
    )


def get_text(
    driver,
    selector,
    by="css selector",
    timeout=settings.LARGE_TIMEOUT
):
    if __is_cdp_swap_needed(driver):
        return driver.cdp.get_text(selector)
    element = wait_for_element(
        driver=driver,
        selector=selector,
        by=by,
        timeout=timeout,
    )
    element_text = element.text
    if shared_utils.is_safari(driver):
        if element.tag_name.lower() in ["input", "textarea"]:
            element_text = element.get_attribute("value")
        else:
            element_text = element.get_attribute("innerText")
    elif element.tag_name.lower() in ["input", "textarea"]:
        element_text = element.get_property("value")
    return element_text
