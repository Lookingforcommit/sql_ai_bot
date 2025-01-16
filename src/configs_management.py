import os
import dotenv
from typing import Optional


class ConfigsManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self):
        self.bot_token: Optional[str] = None
        self.db_path: Optional[str] = None
        self.migrations_dir: Optional[str] = None
        self._load_configs()

    def _load_configs(self):
        dotenv.load_dotenv()
        self.bot_token = os.getenv("BOT_TOKEN")
        self.db_path = os.getenv("DB_PATH")
        self.migrations_dir = os.getenv("MIGRATIONS_DIR")
