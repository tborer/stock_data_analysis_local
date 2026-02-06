import json
import os
import hashlib

class StateManager:
    def __init__(self, state_file="processed_urls.json"):
        self.state_file = state_file
        self.processed = self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                try:
                    return set(json.load(f))
                except json.JSONDecodeError:
                    return set()
        return set()

    def save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(list(self.processed), f)

    def is_processed(self, url):
        return url in self.processed

    def mark_processed(self, url):
        self.processed.add(url)
        self.save_state()
