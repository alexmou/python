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
            if not date_str:
                raise ValueError("Date string cannot be empty")

            parsed_date = parse(date_str)
            if not parsed_date.tzinfo:
                return self.timezone.localize(parsed_date)
            return parsed_date

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
            filtered_elements = []

            for element in elements:
                try:
                    message = Post(element)
                    post_date = message.get_date().get("datetime")

                    if post_date is None:
                        continue

                    # Приводим обе даты к одному часовому поясу для корректного сравнения
                    post_date = post_date.astimezone(self.timezone)
                    start_date = self.start_date.astimezone(self.timezone)

                    if post_date >= start_date:
                        if self.finish_date is None:
                            filtered_elements.append(element)
                        else:
                            finish_date = self.finish_date.astimezone(self.timezone)
                            if post_date <= finish_date:
                                filtered_elements.append(element)

                except Exception as e:
                    print(f"Error filtering element: {str(e)}")
                    continue

            return filtered_elements



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
        :return: JSON string or error message
        """
        try:
            def datetime_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Type {type(obj)} not serializable")

            # Преобразуем в JSON строку
            json_str = json.dumps(self.scraping_result,
                                  default=datetime_serializer,
                                  ensure_ascii=False,
                                  indent=4)

            # Сохраняем в файл (если нужно)
           # with open(path, "w", encoding='utf-8') as outfile:
           #     outfile.write(json_str)

            return json_str  # Возвращаем JSON строку для вывода

        except Exception as e:
            return f"Error saving file: {str(e)}"