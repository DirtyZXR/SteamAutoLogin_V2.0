import json
import threading
from pathlib import Path
from loguru import logger

from shared.config import DatabaseConfig
from shared.db import set_account_online


BACKUP_FILE = "backup.json"
PING_TIMEOUT = 30


class AccountManager:
    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config
        self.backup: dict[str, int] = {}
        self.lock = threading.Lock()
        self._load_backup()

    def _load_backup(self):
        path = Path(BACKUP_FILE)
        if path.exists():
            try:
                with open(path, "r") as f:
                    self.backup = json.load(f)
                logger.info(f"Загружен backup: {self.backup}")
            except json.JSONDecodeError:
                self.backup = {}
                logger.error("Ошибка чтения backup.json, создаём новый")
        else:
            logger.info("backup.json не найден, создаём новый")
            path.touch()

    def _save_backup(self):
        with open(BACKUP_FILE, "w") as f:
            json.dump(self.backup, f, indent=4)

    def mark_online(self, account_id: str):
        account_id = str(account_id)
        with self.lock:
            if account_id in self.backup:
                self.backup[account_id] = 1
            else:
                if set_account_online(self.db_config, int(account_id), online=True):
                    self.backup[account_id] = 1
            self._save_backup()

    def check_offline_cycle(self):
        for account_id in list(self.backup):
            logger.info(f"{account_id}, статус: {self.backup[account_id]}")
            if self.backup[account_id] == 0:
                if set_account_online(self.db_config, int(account_id), online=False):
                    logger.info(f"Аккаунт {account_id} -> offline")
                    with self.lock:
                        self.backup.pop(account_id, None)
            else:
                self.backup[account_id] = 0
        self._save_backup()
