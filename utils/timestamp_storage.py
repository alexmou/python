
# ───────────────────────────────────────────────
# Module: timestamp_storage.py
# ───────────────────────────────────────────────

import os
import json

class TimestampStorage:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def get(self, channel_name: str) -> int:
        return self.data.get(channel_name, 0)

    def update(self, channel_name: str, timestamp: int):
        self.data[channel_name] = timestamp
        self._save()

    def _save(self):
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)