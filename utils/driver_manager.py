import os
import glob
import shutil
import tempfile

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class TelegramDriverManager:
    def __init__(self, user_data_dir: str = None, headless: bool = False):
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.temp_profile_dir = None

    def _clean_chrome_locks(self, path: str):
        """Удаляем .lock файлы из профиля"""
        if not os.path.exists(path):
            return
        patterns = ["SingletonLock", "SingletonCookieLock", "SingletonSocket", "*.tmp", "*.log"]
        for pattern in patterns:
            for p in glob.glob(os.path.join(path, pattern)):
                try:
                    os.remove(p)
                except Exception:
                    pass

    def _create_temp_profile(self):
        """Создаём копию профиля в новую временную директорию"""
        if not self.user_data_dir:
            return None
        temp_dir = tempfile.mkdtemp()
        try:
            shutil.copytree(self.user_data_dir, temp_dir, dirs_exist_ok=True)
            self._clean_chrome_locks(temp_dir)
        except Exception:
            pass
        return temp_dir

    def build_driver(self):
        options = Options()

        if self.headless:
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--headless=new")
            options.add_argument(
                "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            )

        # ❗️ Вот здесь создаём копию профиля
        if self.user_data_dir:
            self.temp_profile_dir = self._create_temp_profile()
            if self.temp_profile_dir:
                options.add_argument(f"--user-data-dir={self.temp_profile_dir}")
                options.add_argument("--profile-directory=Default")

        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(120)

        return driver

    def cleanup(self):
        """Удаляем временную папку после работы драйвера"""
        if self.temp_profile_dir and os.path.exists(self.temp_profile_dir):
            shutil.rmtree(self.temp_profile_dir, ignore_errors=True)
