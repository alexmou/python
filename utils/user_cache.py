
# ───────────────────────────────────────────────
# Module: user_cache.py
# ───────────────────────────────────────────────

import pickle

class UserCache:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.cache = self._load()

    def _load(self):
        try:
            with open(self.filepath, 'rb') as f:
                return pickle.load(f)
        except Exception:
            return {}

    def get(self, user_id: str):
        return self.cache.get(user_id)

    def set(self, user_id: str, data: dict):
        self.cache[user_id] = data
        self._save()

    def _save(self):
        with open(self.filepath, 'wb') as f:
            pickle.dump(self.cache, f)