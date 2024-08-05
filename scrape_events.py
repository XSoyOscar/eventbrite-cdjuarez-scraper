from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

import os
import sqlite3
import sys


WAIT_TIME = 10

EVENTS_LIST_XPATH = "//div[@class='search-results-panel-content__events']/section//div[contains(@class, 'discover-search-desktop-card')]//section[@class='event-card-details']"
TITLE_XPATH = ".//h3"
DATE_XPATH = ".//h3/parent::a/following-sibling::p[1]"
LOCATION_XPATH = ".//h3/parent::a/following-sibling::p[2]"
PRICE_XPATH = ".//div[contains(@class, 'priceWrapper')]/p"
NEXT_PAGE_BUTTON_XPATH = "//li[@data-testid='page-next-wrapper']/button"

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")

driver = webdriver.Chrome(options=chrome_options)
base_url = "https://www.eventbrite.com/d/mexico--ciudad-juarez/all-events/?page="

os.makedirs("data", exist_ok=True)

db_path = "data/events.db"
if os.path.exists(db_path):
    os.remove(db_path)

with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            date TEXT,
            location TEXT,
            price TEXT
        )
    """
    )

    def get_text_or_na(element, xpath):
        try:
            return WebDriverWait(element, WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            ).text.strip()
        except (TimeoutException, NoSuchElementException):
            return "N/A"

    page = 1
    try:
        while True:
            driver.get(f"{base_url}{page}")

            try:
                events_list = WebDriverWait(driver, WAIT_TIME).until(
                    EC.presence_of_all_elements_located((By.XPATH, EVENTS_LIST_XPATH))
                )
            except TimeoutException:
                print(f"Events not found on page {page}")
                break

            for event in events_list:
                title = get_text_or_na(event, TITLE_XPATH)
                date = get_text_or_na(event, DATE_XPATH)
                location = get_text_or_na(event, LOCATION_XPATH)
                price = get_text_or_na(event, PRICE_XPATH)

                cursor.execute(
                    """
                    INSERT INTO events (title, date, location, price)
                    VALUES (?, ?, ?, ?)
                    """,
                    (title, date, location, price),
                )

            try:
                next_page_button = WebDriverWait(driver, WAIT_TIME).until(
                    EC.presence_of_element_located((By.XPATH, NEXT_PAGE_BUTTON_XPATH))
                )
                if next_page_button.is_enabled():
                    next_page_button.click()
                    page += 1
            except (TimeoutException, NoSuchElementException):
                break
    except WebDriverException as e:
        print(f"WebDriverException occurred: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    sys.stdout.flush()