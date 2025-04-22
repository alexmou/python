# utils/post_parser.py (refactored)

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
import time
import pyperclip
from utils.log_config import logger

class Post:
    def __init__(self, element):
        self.el = element

    def get_post_id(self):
        return self.el.get_attribute("data-mid")

    def get_timestamp(self):
        try:
            return int(self.el.get_attribute("data-timestamp"))
        except:
            return 0

    def get_text(self):
        try:
            container = self.el.find_element(By.CSS_SELECTOR, "div.message.spoilers-container")
            text = container.text.strip()
            return text
        except:
            return ""

    def get_media(self):
        photos = []
        try:
            for el in self.el.find_elements(By.CLASS_NAME, "media-photo"):
                src = el.get_attribute("src")
                if src:
                    photos.append(src)
        except:
            pass
        return photos

    def get_author_id(self):
        try:
            group = self.el.find_element(By.XPATH, "./ancestor::div[contains(@class, 'bubbles-group')]")
            avatar_div = group.find_element(By.CSS_SELECTOR, ".bubbles-group-avatar[data-peer-id]")
            return avatar_div.get_attribute("data-peer-id")
        except:
            return ""

    def get_post_link(self, driver):
        try:
            driver.execute_script("document.body.click()")
            time.sleep(0.3)
            msg = self.el.find_element(By.CSS_SELECTOR, ".message")
            driver.execute_script("arguments[0].scrollIntoView(true);", msg)
            time.sleep(0.3)
            ActionChains(driver).move_to_element(msg).context_click().perform()
            WebDriverWait(driver, 180).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.btn-menu-items"))
            )
            items = driver.find_elements(By.CSS_SELECTOR, "div.btn-menu-item")
            for i in items:
                label = i.find_element(By.CSS_SELECTOR, ".btn-menu-item-text").text.strip()
                if "Copy Message Link" in label:
                    i.click()
                    time.sleep(1)
                    return pyperclip.paste()
        except Exception as e:
            logger.warning("Failed to get post link", exc_info=e)
        return ""

    def get_user_info(self, driver, cache, user_id):
        cached = cache.get(user_id)
        if cached:
            return cached

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

        result = {
            "user_id": user_id,
            "user_username": username,
            "user_photo": avatar
        }
        cache.set(user_id, result)
        return result

    def to_dict(self, driver, url, cache):
        post_id = self.get_post_id()
        timestamp = self.get_timestamp()
        text = self.get_text()
        media = self.get_media()
        post_link = self.get_post_link(driver)
        author_id = self.get_author_id()
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
