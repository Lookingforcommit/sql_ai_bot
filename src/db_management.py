import sqlite3
import os

from src.configs_management import ConfigsManager


class DBConnector:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init__()
            cls._instance._run_migrations()
        return cls._instance

    def __init__(self):
        configs_manager = ConfigsManager()
        self.db_path = configs_manager.db_path
        self.migrations_dir = configs_manager.migrations_dir
        self._connection = None

    def _run_migrations(self):
        if not os.path.exists(self.migrations_dir):
            raise FileNotFoundError(f"Директория миграций '{self.migrations_dir}' не найдена.")
        conn = self.get_connection()
        cursor = conn.cursor()
        for filename in sorted(os.listdir(self.migrations_dir)):
            migration_path = os.path.join(self.migrations_dir, filename)
            with open(migration_path, "r", encoding="utf-8") as file:
                sql_script = file.read()
                try:
                    cursor.executescript(sql_script)
                    print(f"Миграция '{filename}' успешно выполнена.")
                except sqlite3.Error as e:
                    print(f"Ошибка выполнения миграции '{filename}': {e}")
        conn.commit()

    def get_connection(self):
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
        return self._connection

    def close_connection(self):
        if self._connection:
            self._connection.close()
            self._connection = None
