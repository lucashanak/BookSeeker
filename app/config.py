import os

APP_VERSION = "1.0.0"
DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
PROWLARR_URL = os.environ.get("PROWLARR_URL", "http://prowlarr:9696")
PROWLARR_API_KEY = os.environ.get("PROWLARR_API_KEY", "")
QBIT_URL = os.environ.get("QBIT_URL", "http://qbittorrent:8081")
QBIT_USER = os.environ.get("QBIT_USER", "admin")
QBIT_PASS = os.environ.get("QBIT_PASS", "adminadmin")
ABS_URL = os.environ.get("ABS_URL", "http://audiobookshelf:80")
ABS_USER = os.environ.get("ABS_USER", "")
ABS_PASS = os.environ.get("ABS_PASS", "")
AUDIOBOOK_DIR = os.environ.get("AUDIOBOOK_DIR", "/audiobooks")
EBOOK_DIR = os.environ.get("EBOOK_DIR", "/ebooks")
QBIT_SAVE_PATH = os.environ.get("QBIT_SAVE_PATH", "")  # Path from qBittorrent's perspective
QBIT_EBOOK_SAVE_PATH = os.environ.get("QBIT_EBOOK_SAVE_PATH", "")  # qBit perspective for ebooks
CALIBRE_URL = os.environ.get("CALIBRE_URL", "http://calibre-web:8083")
