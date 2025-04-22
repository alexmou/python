
# ───────────────────────────────────────────────
# Module: telegram_parser.py
# ───────────────────────────────────────────────

import os
import time
import json
import traceback
from datetime import datetime
from dateutil.parser import parse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.driver_manager import TelegramDriverManager
from utils.timestamp_storage import TimestampStorage
from utils.user_cache import UserCache
from utils.post_parser import Post
from utils.log_config import logger

class TelegramPrivateChannelParser:
    def __init__(self, channel_name, session_dir, timestamp_file, cookies_file="cookies.pkl"):
        self.channel_name = channel_name
        self.URL = f"https://web.telegram.org/k/#@{channel_name}"
        self.session_dir = session_dir
        self.cookies_file = cookies_file
        self.driver = TelegramDriverManager(user_data_dir=session_dir).build_driver()
        self.timestamps = TimestampStorage(timestamp_file)
        self.user_cache = UserCache(os.path.join(session_dir, "user_cache.pkl"))
        self.scraping_result = []

    def _parse_and_localize_date(self, date_str, timezone):
        dt = parse(date_str)
        return dt if dt.tzinfo else timezone.localize(dt)

    def _scroll_to_load_all_messages(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(3)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def _filter_elements(self, elements):
        ts = self.timestamps.get(self.channel_name)
        result = []
        for el in elements:
            ts_str = el.get_attribute("data-timestamp")
            if ts_str and ts_str.isdigit():
                try:
                    el_ts = int(ts_str)
                    if el_ts > ts:
                        result.append(el)
                except ValueError:
                    continue
        return result


    def scrape(self):
        try:
            self.driver.get(self.URL)
            WebDriverWait(self.driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, "bubbles-group")))
            self._scroll_to_load_all_messages()

            bubbles = self.driver.find_elements(By.CLASS_NAME, "bubble")
            logger.info(f"Loaded {len(bubbles)} messages")
            filtered = self._filter_elements(bubbles)

            latest_ts = 0
            for el in filtered:
                try:
                    post = Post(el)
                    data = post.to_dict(self.driver, self.URL, self.user_cache)
                    ts = int(data.get("timestamp", 0))
                    if ts > latest_ts:
                        latest_ts = ts
                    self.scraping_result.append(data)
                    time.sleep(1)
                except Exception as e:
                    logger.warning("Failed to parse a post", exc_info=e)

            if latest_ts:
                self.timestamps.update(self.channel_name, latest_ts)

            return self.scraping_result

        except Exception as e:
            logger.error("Scraping failed", exc_info=e)
            return None

    def save(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.scraping_result, f, ensure_ascii=False, indent=2)

    def close(self):
        self.driver.quit()