import json
import pickle
import os
import time
from datetime import datetime
from dateutil.parser import parse
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional, List, Dict, Any
import traceback
import pyperclip

from utils.post_parser import Post

class TelegramPrivateChannelParser:
    def __init__(
            self,
            channel_name: str,
            start_date: str,
            finish_date: Optional[str] = None,
            timezone: str = 'US/Eastern',
            cookies_file: str = "",
            session_dir: str = "",
            timestamp_dir: str ="",
            get_media: bool = True,
            get_text: bool = True,
            get_meta: bool = True,
            get_user: bool = True
    ):
        self.timestamp_dir = timestamp_dir
        self.channel_name = channel_name
        self.URL = f"https://web.telegram.org/k/#@{channel_name}"
        self.timezone = pytz.timezone(timezone)
        self.start_date = self._parse_and_localize_date(start_date)
        self.finish_date = self._parse_and_localize_date(finish_date) if finish_date else None
        self.cookies_file = cookies_file
        self.session_dir = session_dir
        self.get_media = get_media
        self.get_text = get_text
        self.get_meta = get_meta
        self.get_user = get_user
        self.scraping_result: List[Dict[str, Any]] = []
        self.driver = self._init_driver()
        self.user_cache_file = os.path.join(self.session_dir, "user_cache.pkl")
        self.user_cache: Dict[str, Dict[str, str]] = self._load_user_cache()
        self.timestamp_store_file = os.path.join(self.timestamp_dir, "timestamps")
        self.last_timestamps = self._load_timestamps()

    def _parse_and_localize_date(self, date_str: str) -> datetime:
        if not date_str:
            raise ValueError("Date string cannot be empty")
        parsed_date = parse(date_str)
        return parsed_date.astimezone(self.timezone) if parsed_date.tzinfo else self.timezone.localize(parsed_date)

    def _init_driver(self) -> webdriver.Chrome:
        chrome_options = Options()
        #chrome_options.add_argument("--headless=new")  # Новый headless режим
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument(f"--user-data-dir={self.session_dir}")
        chrome_options.add_argument("--profile-directory=Default")
        chrome_options.add_argument("user-agent=Mozilla/5.0")

        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(120)
        return driver

    def _load_user_cache(self) -> Dict[str, Dict[str, str]]:
        if os.path.exists(self.user_cache_file):
            try:
                with open(self.user_cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print("[DEBUG] Failed to load user cache:", e)
        return {}

    def _save_user_cache(self):
        try:
            with open(self.user_cache_file, 'wb') as f:
                pickle.dump(self.user_cache, f)
        except Exception as e:
            print("[DEBUG] Failed to save user cache:", e)

    def _load_timestamps(self):
        if os.path.exists(self.timestamp_store_file):
            try:
                with open(self.timestamp_store_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_timestamps(self):
        try:
            with open(self.timestamp_store_file, 'w') as f:
                json.dump(self.last_timestamps, f)
        except:
            pass

    def save_cookies(self):
        if not os.path.exists(self.session_dir):
            os.makedirs(self.session_dir)
        cookies = self.driver.get_cookies()
        with open(os.path.join(self.session_dir, self.cookies_file), 'wb') as f:
            pickle.dump(cookies, f)

    def load_cookies(self) -> bool:
        cookies_path = os.path.join(self.session_dir, self.cookies_file)
        if not os.path.exists(cookies_path):
            return False
        try:
            self.driver.get("https://web.telegram.org/")
            time.sleep(3)
            self.driver.delete_all_cookies()
            with open(cookies_path, 'rb') as f:
                for cookie in pickle.load(f):
                    self.driver.add_cookie(cookie)
            self.driver.refresh()
            time.sleep(3)
            return True
        except:
            return False

    def manual_login(self):
        print("Please log in manually...")
        self.driver.get("https://web.telegram.org/")
        WebDriverWait(self.driver, 300).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.tg_head")))
        print("Logged in successfully")
        self.save_cookies()

    def is_logged_in(self) -> bool:
        try:
            self.driver.get("https://web.telegram.org/")
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.tg_head")))
            return True
        except:
            return False

    def _scroll_to_load_all_messages(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(30)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def _filter_elements(self, elements: List[Any]) -> List[Any]:
        result = []
        last_ts = self.last_timestamps.get(self.channel_name, 0)
        for el in elements:
            try:
                ts = int(el.get_attribute("data-timestamp"))
                if ts > last_ts:
                    result.append(el)
            except:
                continue
        return result

    def parse_user_profile_from_id(self, user_id: str) -> Dict[str, str]:
        if user_id in self.user_cache:
            return self.user_cache[user_id]

        profile_url = f"https://web.telegram.org/k/#{user_id}"
        self.driver.get(profile_url)
        time.sleep(2.5)

        username = "unknown"
        photo_url = "unknown"

        try:
            current_url = self.driver.current_url
            if "#" in current_url:
                hash_part = current_url.split("#")[1]
                if hash_part.startswith("@"):
                    username = hash_part[1:]
        except Exception as e:
            print("[DEBUG] Failed to parse username from URL:", e)

        try:
            photo_elem = self.driver.find_element(By.CSS_SELECTOR, "div.chat-info img.avatar-photo")
            photo_url = photo_elem.get_attribute("src")
        except:
            pass

        result = {
            "user_id": user_id,
            "profile_url": profile_url,
            "user_username": username,
            "user_photo": photo_url
        }

        self.user_cache[user_id] = result
        time.sleep(0.3)
        return result

    def generate_post_link(self, post_element) -> str:
        try:
            # Сброс фокуса
            self.driver.execute_script("document.body.click()")
            time.sleep(0.3)

            # Наводим и ПКМ по содержимому
            message_body = post_element.find_element(By.CSS_SELECTOR, ".message")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", message_body)
            time.sleep(0.3)

            actions = ActionChains(self.driver)
            actions.move_to_element(message_body).context_click().perform()
            time.sleep(1)

            # Ожидаем появление меню
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.btn-menu-items"))
            )

            # Ищем пункт "Copy Message Link"
            menu_items = self.driver.find_elements(By.CSS_SELECTOR, "div.btn-menu-item")
            for item in menu_items:
                try:
                    label = item.find_element(By.CSS_SELECTOR, ".btn-menu-item-text").text.strip()
                    if "Copy Message Link" in label:
                        item.click()
                        time.sleep(1)
                        import pyperclip
                        link = pyperclip.paste()
                        print("[DEBUG] Copied message link:", link)
                        return link
                except:
                    continue

            print("[DEBUG] Menu item not found.")
            return ""
        except Exception as e:
            print("[DEBUG] Failed to copy message link:", e)
            return ""


    def _parse_posts(self, elements: List[Any]) -> List[Dict[str, Any]]:
        results = []
        latest_ts = 0
        for el in elements:
            try:
                post = Post(el)
                data = {"channel_url": self.URL, **post.get_post_id()}
                if self.get_text:
                    data.update(post.get_text())
                if self.get_media:
                    data.update(post.get_media())
                if self.get_meta:
                    meta = post.get_date()
                    if isinstance(meta, dict) and isinstance(meta.get('datetime'), datetime):
                        dt = meta['datetime']
                        meta['datetime'] = dt.isoformat()
                        ts = int(dt.timestamp())
                        if ts > latest_ts:
                            latest_ts = ts
                    data.update(meta)
                if self.get_user:
                    author_id = post.get_author_id()
                    if author_id:
                        data.update(self.parse_user_profile_from_id(author_id))
                data["message_link"] = self.generate_post_link(el)
                results.append(data)
                time.sleep(1.2)
            except:
                continue

        if latest_ts:
            self.last_timestamps[self.channel_name] = latest_ts

        return results

    def scrape(self) -> Optional[List[Dict[str, Any]]]:
        try:
            if not self.is_logged_in():
                if not self.load_cookies():
                    self.manual_login()
            self.driver.get(self.URL)
            WebDriverWait(self.driver, 120).until(
                EC.presence_of_element_located((By.CLASS_NAME, "bubbles-group"))
            )
            self._scroll_to_load_all_messages()
            bubbles = self.driver.find_elements(By.CLASS_NAME, "bubble")
            filtered = self._filter_elements(bubbles)
            self.scraping_result = self._parse_posts(filtered)
            self._save_user_cache()
            self._save_timestamps()
            return self.scraping_result
        except Exception as e:
            print(f"Scraping error: {e}")
            traceback.print_exc()
            return None

    def save_results(self, path: str) -> str:
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.scraping_result, f, ensure_ascii=False, indent=4)
            return f"Saved to {path}"
        except Exception as e:
            return f"Error saving file: {e}"

    def close(self):
        self.driver.quit()
