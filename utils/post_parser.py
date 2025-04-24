from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
import pyperclip
import time
from utils.log_config import logger

class Post:
    def __init__(self):
        pass

    def get_post_id(self, el):
        try:
            return el.get_attribute("data-mid")
        except Exception as e:
            logger.warning("[stale] get_post_id", exc_info=e)
            return None

    def get_timestamp(self, el):
        try:
            ts = el.get_attribute("data-timestamp")
            return int(ts) if ts else 0
        except:
            return 0

    def get_text(self, el):
        try:
            container = el.find_element(By.CSS_SELECTOR, "div.message.spoilers-container")
            return container.text.strip()
        except:
            return ""

    def get_media(self, el):
        photos = []
        try:
            for img in el.find_elements(By.CLASS_NAME, "media-photo"):
                src = img.get_attribute("src")
                if src:
                    photos.append(src)
        except:
            pass
        return photos

    def get_author_id(self, el):
        try:
            group = el.find_element(By.XPATH, "./ancestor::div[contains(@class, 'bubbles-group')]")
            avatar_div = group.find_element(By.CSS_SELECTOR, ".bubbles-group-avatar[data-peer-id]")
            return avatar_div.get_attribute("data-peer-id")
        except:
            return ""

    def get_user_info(self, driver, cache, user_id):
        if user_id in cache:
            return cache[user_id]

        profile_url = f"https://web.telegram.org/k/#{user_id}"
        driver.get(profile_url)
        time.sleep(2)

        username = "unknown"
        avatar = "unknown"

        try:
            current_url = driver.current_url
            if current_url.startswith("https://web.telegram.org/k/#@"):
                username = current_url.split("#@")[-1]
        except:
            pass

        try:
            photo_elem = driver.find_element(By.CSS_SELECTOR, "div.chat-info img.avatar-photo")
            avatar = photo_elem.get_attribute("src")
        except:
            pass

        info = {
            "user_id": user_id,
            "user_username": username,
            "user_photo": avatar
        }
        cache[user_id] = info
        return info

    def get_post_link(self, el, driver) -> str:
        try:
            driver.execute_script("document.body.click()")  # сброс фокуса
            time.sleep(0.3)

            # Находим, куда кликать правой кнопкой
            try:
                msg = el.find_element(By.CSS_SELECTOR, ".message")
            except:
                msg = el.find_element(By.CSS_SELECTOR, ".bubble-content")

            driver.execute_script("arguments[0].scrollIntoView(true);", msg)
            time.sleep(0.3)
            ActionChains(driver).move_to_element(msg).context_click().perform()

            # Увеличенный таймаут + лог
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.btn-menu-items"))
            )

            for item in driver.find_elements(By.CSS_SELECTOR, "div.btn-menu-item"):
                try:
                    label = item.find_element(By.CSS_SELECTOR, ".btn-menu-item-text").text.strip()
                    if "Copy Message Link" in label:
                        item.click()
                        time.sleep(1)
                        return pyperclip.paste()
                except:
                    continue

        except Exception as e:
                print("[DEBUG] Failed to get post link:", e)
        return ""


    def to_dict(self, el, driver, url, cache):
        post_id = self.get_post_id(el)
        timestamp = self.get_timestamp(el)
        text = self.get_text(el)
        media = self.get_media(el)
        post_link = self.get_post_link(el, driver)
        author_id = self.get_author_id(el)
        user_info = self.get_user_info(driver, cache, author_id) if author_id else {}

        return {
            "channel_url": url,
            "post_id": post_id,
            "timestamp": timestamp,
            "text": text,
            "photo_urls": media,
            "message_link": post_link,
            **user_info
        }
