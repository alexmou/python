from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import pyperclip
import time
from utils.log_config import logger

class Post:
    def __init__(self):
        pass

    def get_post_id(self, el):
        """Получаем ID сообщения с обработкой stale элемента"""
        try:
            # Обновляем элемент перед работой с ним
            el = self._refresh_element(el)
            if not el:
                return None

            # 1. Проверяем data-mid
            post_id = el.get_attribute("data-mid")
            if post_id:
                return post_id

            # 2. Проверяем data-msg-id
            post_id = el.get_attribute("data-msg-id")
            if post_id:
                return post_id

            # Остальные проверки...

        except Exception as e:
            #logger.error(f"Error getting post ID: {str(e)}")
            return None

    def _refresh_element(self, el):
        """Обновляет stale элемент"""
        try:
            # Получаем ID элемента и находим его заново
            element_id = el.id
            return self.driver.find_element(By.ID, element_id)
        except:
            try:
                # Альтернативный способ через XPath
                xpath = self._get_xpath_for_element(el)
                return self.driver.find_element(By.XPATH, xpath)
            except Exception as e:
                #logger.warning(f"Cannot refresh element: {str(e)}")
                return None

    def get_timestamp(self, el):
        ts = el.get_attribute("data-timestamp")
        try:
            return int(ts) if ts else 0
        except ValueError:
            return 0

    def get_text(self, el):
        # проверяем наличие контейнера спойлеров
        elems = el.find_elements(By.CSS_SELECTOR, "div.message.spoilers-container")
        return elems[0].text.strip() if elems else ""

    def get_media(self, el):
        photos = []
        for img in el.find_elements(By.CLASS_NAME, "media-photo"):
            src = img.get_attribute("src")
            if src:
                photos.append(src)
        return photos

    def get_author_id(self, el):
        # ищем группу пузырей, затем peer-id
        groups = el.find_elements(By.XPATH, "./ancestor::div[contains(@class, 'bubbles-group')]")
        if not groups:
            return ""
        avatars = groups[0].find_elements(By.CSS_SELECTOR, ".bubbles-group-avatar[data-peer-id]")
        return avatars[0].get_attribute("data-peer-id") if avatars else ""

    def get_user_info(self, driver, cache, user_id):
        if user_id in cache:
            return cache[user_id]

        main = driver.current_window_handle
        driver.execute_script("window.open('about:blank','_blank');")
        driver.switch_to.window(driver.window_handles[-1])
        driver.get(f"https://web.telegram.org/k/#{user_id}")

        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.chat-info"))
            )
        except TimeoutException:
            #logger.warning(f"[get_user_info] profile load timeout for {user_id}")
            pass
        # username из URL
        curr = driver.current_url
        username = curr.split("#@")[-1] if "#@" in curr else ""

        # avatar
      #  avatar = ""
      #  avs = driver.find_elements(By.CSS_SELECTOR, "div.chat-info img.avatar-photo")
      #  if avs:
      #      avatar = avs[0].get_attribute("src")

        info = {
            "user_id": user_id,
            "user_username": username
            #"user_photo": avatar
        }
        cache[user_id] = info

        driver.close()
        driver.switch_to.window(main)
        return info

    def get_post_link(self, el, driver) -> str:
        # максимально простой и безопасный способ:
        date_links = el.find_elements(By.CSS_SELECTOR, "a.message_date")
        if date_links:
            return date_links[0].get_attribute("href") or ""

        # если вдруг нет — можно оставить ваш контекст-меню фоллбек здесь
        return ""

    def to_dict(self, el, driver, channel_url, cache):
        data = {
            "channel_url": channel_url,
            "post_id":      self.get_post_id(el),
            "timestamp":    self.get_timestamp(el),
            "text":         self.get_text(el),
            "photo_urls":   self.get_media(el),
            "message_link": self.get_post_link(el, driver),
        }

        author_id = self.get_author_id(el)
        if author_id:
            data.update(self.get_user_info(driver, cache, author_id))
        return data
