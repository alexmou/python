import json
import pytz
import time
from datetime import datetime
from dateutil.parser import parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional, List, Dict, Any

from utils.post_parser import Post


class ChannelParser:
    """
    Provides methods to scrape telegram channel texts + metadata, save a result in JSON.
    """
    def __init__(
            self,
            channel_name: str,
            start_date: str,
            finish_date: Optional[str] = None,
            timezone: str = 'US/Eastern',
            get_media: bool = True,
            get_text: bool = True,
            get_meta: bool = True
    ):
        self.URL = f"https://t.me/s/{channel_name}"
        self.timezone = pytz.timezone(timezone)
        self.start_date = self._parse_and_localize_date(start_date)
        self.finish_date = self._parse_and_localize_date(finish_date) if finish_date else None
        self.get_media = get_media
        self.get_text = get_text
        self.get_meta = get_meta
        self.scraping_result: List[Dict[str, Any]] = []

    def _parse_and_localize_date(self, date_str: str) -> datetime:
        """Parse and localize date string"""
        return self.timezone.localize(parse(date_str))

    def _init_driver(self) -> webdriver.Chrome:
        """Initialize and configure Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(60)
        return driver

    def scrape(self) -> List[Dict[str, Any]]:
        """Scrapes telegram channel content"""
        driver = self._init_driver()
        try:
            driver.get(self.URL)
            time.sleep(5)  # Initial wait

            self._scroll_page(driver)

            posts_elements = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "tgme_widget_message_wrap"))
            )
            filtered_posts_elements = self._filter_elements(posts_elements)
            self.scraping_result = self._parse_posts(filtered_posts_elements)

            return self.scraping_result

        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            raise
        finally:
            driver.quit()

    def _scroll_page(self, driver: webdriver.Chrome) -> None:
        """Improved scrolling implementation"""
        scroll_attempts = 0
        max_attempts = 20

        while scroll_attempts < max_attempts:
            try:
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)

                oldest_post = driver.find_elements(By.CLASS_NAME, "tgme_widget_message_wrap")[-1]
                post_date = parse(oldest_post.find_element(
                    By.CLASS_NAME, "tgme_widget_message_date").find_element(
                    By.TAG_NAME, "time").get_attribute('datetime'))

                if post_date < self.start_date:
                    break

                scroll_attempts += 1

            except Exception as e:
                print(f"Scroll error: {str(e)}")
                break

    def _filter_elements(self, elements: List[Any]) -> List[Any]:
        """Filters posts by date range."""
        start_msg_idx = None

        for i, element in enumerate(elements):
            message = Post(element)
            if self.start_date <= message.get_date()["datetime"]:
                start_msg_idx = i
                break

        if start_msg_idx is None:
            return []

        if self.finish_date is None:
            return elements[start_msg_idx:]

        fin_msg_idx = None
        elements_half_filtered = elements[start_msg_idx:]

        for i, element in enumerate(reversed(elements_half_filtered)):
            message = Post(element)
            if self.finish_date >= message.get_date()['datetime'].astimezone(self.timezone):
                fin_msg_idx = i
                break

        return elements_half_filtered[:len(elements_half_filtered)-fin_msg_idx] if fin_msg_idx is not None else []

    def _parse_posts(self, posts_elements: List[Any]) -> List[Dict[str, Any]]:
        """Parse filtered posts into structured data"""
        post_objects = []

        for post_element in posts_elements:
            post = Post(post_element)
            post_dict = {
                "channel_url": self.URL,
                **post.get_post_id()
            }

            if self.get_media:
                post_dict.update(post.get_media())

            if self.get_text:
                post_dict.update(post.get_text())

            if self.get_meta:
                post_dict.update(post.get_date())

            post_objects.append(post_dict)

        return post_objects

    def save_json(self, path: str) -> str:
        """
        Saves scraping result to JSON file.
        :param path: Absolute file path
        :return: Save status message
        """
        try:
          #  with open(path, "w", encoding='utf-8') as outfile:
           #     json.dump(self.scraping_result, outfile, default=str, ensure_ascii=False, indent=4)
            print(self.scraping_result)
            return "Saved successfully."
        except Exception as e:
            return f"Error saving file: {str(e)}"