import configparser
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _find_file_upwards(filename: str, start_dir: str | None = None) -> Path | None:
    start = Path(start_dir or os.getcwd())
    for parent in [start, *start.parents]:
        candidate = parent / filename
        if candidate.exists():
            return candidate
    return None


def _resolve_path(relative_path: str) -> str:
    p = _find_file_upwards(relative_path)
    if p is not None:
        return str(p)
    return relative_path


@dataclass
class DatabaseConfig:
    host: str = field(default_factory=lambda: os.getenv("DB_HOST", ""))
    user: str = field(default_factory=lambda: os.getenv("DB_USER", ""))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))
    name: str = field(default_factory=lambda: os.getenv("DB_NAME", "accounts"))
    table: str = field(default_factory=lambda: os.getenv("DB_TABLE", "users"))


@dataclass
class TelegramConfig:
    token: str = field(default_factory=lambda: os.getenv("TELEGRAM_TOKEN", ""))
    chat_id: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))

    @property
    def params(self) -> dict[str, str]:
        return {"token": self.token, "chat_id": self.chat_id}


@dataclass
class ServerConfig:
    ip: str = "192.168.88.205"
    port: int = 5000


@dataclass
class SDAConfig:
    path: str = ""


@dataclass
class Settings:
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    sda: SDAConfig = field(default_factory=SDAConfig)
    captcha_key: str = field(default_factory=lambda: os.getenv("CAPTCHA_KEY", ""))

    @classmethod
    def load_client_config(cls, config_path: str | None = None) -> "Settings":
        settings = cls()
        resolved = _resolve_path(config_path or "client/config.ini")
        if Path(resolved).exists():
            config = configparser.ConfigParser()
            config.read(resolved)
            try:
                settings.server.ip = config.get("Settings", "server_ip")
                settings.server.port = int(config.get("Settings", "port"))
            except (configparser.NoSectionError, configparser.NoOptionError):
                pass
        return settings

    @classmethod
    def load_server_config(cls, config_path: str | None = None) -> "Settings":
        settings = cls()
        resolved = _resolve_path(config_path or "server/config_sda.ini")
        if Path(resolved).exists():
            config = configparser.ConfigParser()
            config.read(resolved)
            try:
                settings.sda.path = config.get("SDA", "path_to_SDA")
            except (configparser.NoSectionError, configparser.NoOptionError):
                pass
        return settings


settings = Settings()
