import storage as cp_storage
import json
from logging_ import log

class Storage(dict):
    def __init__(self, filename='data.json'):
        self.filename = filename
        self._data = {}
        self._load_data()

    def _load_data(self):
        """Load data from the JSON file if it exists."""
        try:
            with open(self.filename, 'r') as f:
                self._data = json.load(f)
        except (OSError, ValueError, RuntimeError):
            self._data = {}
            log("Failed to load data from the JSON file.")

    def _save_data(self):
        """Save data to the JSON file."""
        # Switch the filesystem to write mode
        try:
            cp_storage.remount("/", readonly=False)
        except RuntimeError:
            log("Failed to remount the filesystem to write mode.")
            return
        with open(self.filename, 'w') as f:
            json.dump(self._data, f)
        # Switch the filesystem back to read-only mode
        cp_storage.remount("/", readonly=True)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value
        self._save_data()

    def __delitem__(self, key):
        del self._data[key]
        self._save_data()

    def __contains__(self, key):
        return key in self._data

    def __iter__(self):
        return iter(self._data)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def get(self, key, default=None):
        return self._data.get(key, default)

    def clear(self):
        self._data.clear()
        self._save_data()


# Storage instance
storage = Storage()
