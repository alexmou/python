import os
import shutil

# ───────────────────────────────────────────────
# Module: driver_manager.py
# ───────────────────────────────────────────────

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class TelegramDriverManager:
    def __init__(self, user_data_dir: str = None, headless: bool = False):
        self.user_data_dir = user_data_dir
        self.headless = headless

    def _clean_chrome_locks(self):
        if not self.user_data_dir:
            return
        for fname in ["SingletonLock", "lockfile"]:
            try:
                os.remove(os.path.join(self.user_data_dir, fname))
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"[DEBUG] Не удалось удалить {fname}: {e}")

    def build_driver(self):
        self._clean_chrome_locks()

        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        options.add_argument("user-agent=Mozilla/5.0")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        if self.user_data_dir:
            os.makedirs(self.user_data_dir, exist_ok=True)
            options.add_argument(f"--user-data-dir={self.user_data_dir}")
            options.add_argument("--profile-directory=Default")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(120)
        return driver
