import os
import json
import time
from datetime import datetime
import shutil
import pyperclip
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException
from utils.driver_manager import TelegramDriverManager
from utils.post_parser import Post

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

    def debug_screenshot(self, label: str):
        ts = int(time.time())
        filename = f"/home/l_murygin/p8/debug_{label}_{ts}.png"
        self.driver.save_screenshot(filename)
        print(f"[DEBUG] Saved screenshot {filename}")

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
            except:
                pass
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
            self.driver.execute_script("document.body.click()")
            time.sleep(0.5)

            try:
                msg = el.find_element(By.CSS_SELECTOR, ".message")
            except NoSuchElementException:
                msg = el.find_element(By.CSS_SELECTOR, ".bubble-content")

            self.driver.execute_script("arguments[0].scrollIntoView(true);", msg)
            time.sleep(0.4)
            ActionChains(self.driver).move_to_element(msg).context_click().perform()

            WebDriverWait(self.driver, 6).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.btn-menu-items"))
            )

            for item in self.driver.find_elements(By.CSS_SELECTOR, "div.btn-menu-item"):
                try:
                    label = item.find_element(By.CSS_SELECTOR, ".btn-menu-item-text").text.strip()
                    if "Copy Message Link" in label:
                        item.click()
                        time.sleep(1)
                        return pyperclip.paste()
                except:
                    continue

        except (StaleElementReferenceException, NoSuchElementException, TimeoutException) as e:
            print(f"[WARN] get_post_link menu fail: {e}")
            self.debug_screenshot("error_get_link")
            pass
        return ""

    def check_authorization_or_capture_qr(self):
        """Проверяет, авторизован ли пользователь. Если нет, сохраняет скриншот QR-кода и завершает выполнение."""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.tg_head"))
            )
            print("[INFO] Пользователь авторизован.")
        except TimeoutException:
            # Если шапка не найдена — скорее всего страница авторизации
            filename = f"/home/l_murygin/p8/qr_code.png"
            self.driver.save_screenshot(filename)
            print(f"[WARNING] Пользователь НЕ авторизован! QR-код сохранён в файл: {filename}")
            #self.close()
            #exit(1)

    def scrape(self):
        self.driver.get(self.url)
        self.check_authorization_or_capture_qr()
        # Ждем полной загрузки интерфейса Telegram
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "tg_head"))
            )


        except TimeoutException:
            print("[WARN] Telegram UI не загрузился")

        self.debug_screenshot("after_tg_load")

        self._scroll_page()

        posts = self.driver.find_elements(By.CLASS_NAME, "bubble")
        filtered = self._filter_elements(posts)

        print(f"[INFO] Найдено {len(filtered)} новых постов")

        post_handler = Post()
        latest_ts = 0

        for el in filtered:
            try:
                self.close_user_profile_if_open()
                time.sleep(0.4)

                link = self.get_post_link(el)
                data = post_handler.to_dict(el, self.driver, self.url, self.user_cache)
                data["message_link"] = link

                if data["timestamp"] > latest_ts:
                    latest_ts = data["timestamp"]
                self.result.append(data)

                time.sleep(1.0)
            except Exception as e:
                print(f"[WARN] Ошибка при обработке поста: {e}")
                self.debug_screenshot("post_parse_error")
                continue

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

        self.debug_screenshot("after_scroll")

    def save(self, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.result, f, ensure_ascii=False, indent=2)



    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
        # Удаляем временную папку, если она была создана
        if hasattr(self.driver, "temp_user_data_dir") and self.driver.temp_user_data_dir:
            shutil.rmtree(self.driver.temp_user_data_dir, ignore_errors=True)

