import os
import json
import time
from datetime import datetime

import pyperclip
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException
from utils.driver_manager import TelegramDriverManager
from utils.post_parser import Post
from utils.log_config import logger

class TelegramPrivateChannelParser:
    def __init__(self, channel_name: str, session_dir: str, timestamp_file: str):
        self.channel_name = channel_name
        self.session_dir = session_dir
        self.timestamp_file = timestamp_file
        self.url = f"https://web.telegram.org/k/#@{channel_name}"

        self.driver = TelegramDriverManager(user_data_dir=session_dir).build_driver()
        self.timestamps = self._load_timestamps()
        self.user_cache = {}
        self.result = []

    def _load_timestamps(self):
        if os.path.exists(self.timestamp_file):
            try:
                with open(self.timestamp_file, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_timestamps(self):
        with open(self.timestamp_file, "w") as f:
            json.dump(self.timestamps, f)

    def _filter_elements(self, elements):
        ts = self.timestamps.get(self.channel_name, 0)
        post = Post()
        valid = []
        for el in elements:
            try:
                t = post.get_timestamp(el)
                if t > ts:
                    valid.append(el)
            except Exception as e:
                logger.warning("[WARN] bad timestamp", exc_info=e)
        return valid

    def close_user_profile_if_open(self):
        try:
            close_btn = self.driver.find_element(By.CSS_SELECTOR, ".chat-info .Icon.icon-close")
            self.driver.execute_script("arguments[0].click();", close_btn)
            time.sleep(0.5)
        except:
            pass

    def get_post_link(self, el) -> str:
        try:
            self.driver.execute_script("document.body.click()")  # Сброс фокуса
            time.sleep(0.3)

            # Поиск элемента сообщения
            try:
                msg = el.find_element(By.CSS_SELECTOR, ".message")
            except NoSuchElementException:
                msg = el.find_element(By.CSS_SELECTOR, ".bubble-content")

            # Прокрутка к элементу
            self.driver.execute_script("arguments[0].scrollIntoView(true);", msg)
            time.sleep(0.5)

            # Вызов контекстного меню
            ActionChains(self.driver).move_to_element(msg).context_click().perform()

            # Ожидание появления меню
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.btn-menu-items"))
            )

            # Поиск и клик по пункту меню
            for item in self.driver.find_elements(By.CSS_SELECTOR, "div.btn-menu-item"):
                try:
                    label = item.find_element(By.CSS_SELECTOR, ".btn-menu-item-text").text.strip()
                    if "Copy Message Link" in label:
                        item.click()
                        time.sleep(1)
                        return pyperclip.paste()
                except Exception:
                    continue

        except Exception as e:
            logger.warning("[get_post_link] menu fail", exc_info=e)
            self.driver.save_screenshot(f"./debug_link_error_{int(time.time())}.png")

        return ""

    def scrape(self):
        self.driver.get(self.url)

        for _ in range(3):
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "bubbles-group"))
                )
                break
            except:
                time.sleep(2)

        self._scroll_page()

        posts = self.driver.find_elements(By.CLASS_NAME, "bubble")
        filtered = self._filter_elements(posts)

        logger.info(f"[INFO] Найдено {len(filtered)} новых постов")

        post_handler = Post()
        latest_ts = 0

        for el in filtered:
            try:
                self.close_user_profile_if_open()
                time.sleep(0.4)

                link = self.get_post_link(el)
                logger.debug(f"[DEBUG] link: {link}")
                data = post_handler.to_dict(el, self.driver, self.url, self.user_cache)
                data["message_link"] = link

                logger.debug(f"[POST] ID: {data.get('post_id')}, TS: {data.get('timestamp')}, LINK: {data['message_link']}")

                if data["timestamp"] > latest_ts:
                    latest_ts = data["timestamp"]
                self.result.append(data)
                time.sleep(1.0)
            except Exception as e:
                logger.warning("[WARN] Ошибка при обработке поста", exc_info=e)

        if latest_ts:
            self.timestamps[self.channel_name] = latest_ts
            self._save_timestamps()

        return self.result

    def _scroll_page(self):
        last_height = -1
        same_count = 0
        max_retries = 30

        for _ in range(max_retries):
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(3)
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            if current_height == last_height:
                same_count += 1
            else:
                same_count = 0
            if same_count >= 5:
                break
            last_height = current_height

    def save(self, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.result, f, ensure_ascii=False, indent=2)

    def close(self):
        self.driver.quit()
