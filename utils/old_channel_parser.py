import json
import pytz
import time
from dateutil.parser import parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from utils.post_parser import Post


class ChannelParser(object):
    """
    Provides methods to scrape telegram channel texts + metadata, save a result in JSON.
    """
    def __init__(self,
                 channel_name,
                 start_date,
                 finish_date,
                 timezone='US/Eastern',
                 get_media=True,
                 get_text=True,
                 get_meta=True):
        self.URL = "https://t.me/s/" + channel_name
        self.timezone = pytz.timezone(timezone)
        self.start_date = parse(start_date)
        self.start_date = self.timezone.localize(self.start_date)
        self.finish_date = self.timezone.localize(parse(finish_date)) if finish_date else None
        self.get_media = get_media
        self.get_text = get_text
        self.get_meta = get_meta

    def _init_driver(self):
        """Initialize and configure Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # Новый headless режим
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

    def scrape(self):
        """Scrapes telegram channel content"""
        driver = self._init_driver()
        try:
            #print("Loading page...")
            driver.get(self.URL)
            time.sleep(5)  # Initial wait

            #print("Scrolling to load older posts...")
            self._scroll_page(driver)

            #print("Collecting posts...")
            posts_elements = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "tgme_widget_message_wrap")))
            filtered_posts_elements = self._filter_elements(posts_elements)
            self.scraping_result = self._parse_posts(filtered_posts_elements)

            return self.scraping_result

        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            raise
        finally:
            driver.quit()

    def _scroll_page(self, driver):
        """Improved scrolling implementation"""
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 20

        while scroll_attempts < max_attempts:
            try:
                # Плавный скролл через JavaScript
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)  # Даем время для загрузки контента

                # Проверяем дату самого старого поста
                oldest_post = driver.find_elements(By.CLASS_NAME, "tgme_widget_message_wrap")[-1]
                post_date = parse(oldest_post.find_element(
                    By.CLASS_NAME, "tgme_widget_message_date").find_element(
                    By.TAG_NAME, "time").get_attribute('datetime'))


                utc=pytz.UTC
               # post_date = utc.localize(post_date)
                #print(post_date)
                #print(self.start_date)
                if post_date < self.start_date:
                    break

                scroll_attempts += 1

            except Exception as e:
                print(f"Scroll error: {str(e)}")
                break
    def _filter_elements(self, elements):
        """
        Filters posts by date range.
        :param elements: Posts elements to filter
        :return: Filtered list of posts
        """

        start_msg_idx = None

        for i, element in enumerate(elements):
            message = Post(element)
            utc=pytz.UTC
            datetime_start = self.start_date
            datetime_message = message.get_date()["datetime"]

            if datetime_start <= datetime_message:
               start_msg_idx = i
            break

        if self.finish_date is None:
            return elements[start_msg_idx:]
        else:
            fin_msg_idx = None
            elements_half_filtered = elements[start_msg_idx:]
            elements_half_filtered.reverse()
            for i, element in enumerate(elements_half_filtered):
                message = Post(element)
                if self.finish_date >= message.get_date()['datetime'].astimezone(self.timezone):
                    fin_msg_idx = i
                    break
            return elements_half_filtered[fin_msg_idx:]
    def _parse_posts(self, posts_elements):
        """Parse filtered posts into structured data"""
        post_objects = []
        for post_element in posts_elements:
            post = Post(post_element)

            post_dict = dict()
            post_id = post.get_post_id()
            post_dict.update({"channel_url": self.URL})
            post_dict.update(post_id)

            if self.get_media:
                media_data = post.get_media()
                post_dict.update(media_data)

            if self.get_text:
                post_text = post.get_text()
                post_dict.update(post_text)

            if self.get_meta:
                date = post.get_date()
                post_dict.update(date)

                #views = post.get_views()
                #post_dict.update(views)

                #is_reply = post.is_reply()
                #post_dict.update(is_reply)

                #is_forwarded = post.is_forwarded()
                #post_dict.update(is_forwarded)

                #is_edited = post.is_edited()
                #post_dict.update(is_edited)

            post_objects.append(post_dict)

        return post_objects
    def save_json(self, path):
        """
        Saves scraping result to JSON file.
        :param path: Absolute file path
        :return: Save status message
        """
        try:
            with open(path, "w", encoding='utf8') as outfile:
                json.dump(self.scraping_result, outfile, default=str, ensure_ascii=False, indent=4)
                print(self.scraping_result)
            return "Saved successfully."
        except Exception as e:
            return f"Error saving file: {str(e)}"
