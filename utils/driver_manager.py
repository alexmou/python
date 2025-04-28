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
        self.temp_user_data_dir = None  # временная папка

    def _clean_chrome_locks(self, directory):
        patterns = [
            "SingletonLock",
            "SingletonCookieLock",
            "SingletonSocket",
            "*.tmp",
            "*.log",
        ]
        for pattern in patterns:
            for path in glob.glob(os.path.join(directory, pattern)):
                try:
                    os.remove(path)
                except Exception:
                    pass  # игнорируем ошибки

    def build_driver(self):
        options = Options()

        if self.user_data_dir:
            # Копируем оригинальную папку cookies в temp-папку
            self.temp_user_data_dir = tempfile.mkdtemp(prefix="chrome_profile_")
            shutil.copytree(self.user_data_dir, self.temp_user_data_dir, dirs_exist_ok=True)
            self._clean_chrome_locks(self.temp_user_data_dir)
            options.add_argument(f"--user-data-dir={self.temp_user_data_dir}")
            options.add_argument("--profile-directory=Default")

        if self.headless:
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")

        options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(120)

        # Присваиваем путь для последующего удаления
        driver.temp_user_data_dir = self.temp_user_data_dir

        return driver
