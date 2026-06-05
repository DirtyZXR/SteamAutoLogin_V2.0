import os
import tempfile

from shared.config import DatabaseConfig, Settings, TelegramConfig


class TestDatabaseConfig:
    def test_defaults_from_env(self, monkeypatch):
        monkeypatch.setenv("DB_HOST", "10.0.0.1")
        monkeypatch.setenv("DB_USER", "testuser")
        monkeypatch.setenv("DB_PASSWORD", "testpass")
        monkeypatch.setenv("DB_NAME", "testdb")
        monkeypatch.setenv("DB_TABLE", "testtable")

        cfg = DatabaseConfig()
        assert cfg.host == "10.0.0.1"
        assert cfg.user == "testuser"
        assert cfg.password == "testpass"
        assert cfg.name == "testdb"
        assert cfg.table == "testtable"

    def test_defaults_when_no_env(self, monkeypatch):
        for key in ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME", "DB_TABLE"]:
            monkeypatch.delenv(key, raising=False)
        cfg = DatabaseConfig()
        assert cfg.host == ""
        assert cfg.name == "accounts"
        assert cfg.table == "users"


class TestTelegramConfig:
    def test_params(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_TOKEN", "tok123")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "456")
        cfg = TelegramConfig()
        assert cfg.params == {"token": "tok123", "chat_id": "456"}

    def test_empty_params(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        cfg = TelegramConfig()
        assert cfg.params == {"token": "", "chat_id": ""}


class TestSettings:
    def test_default_settings(self, monkeypatch):
        for key in [
            "DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME", "DB_TABLE",
            "TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID", "CAPTCHA_KEY",
        ]:
            monkeypatch.delenv(key, raising=False)
        s = Settings()
        assert s.db.host == ""
        assert s.server.ip == "192.168.88.205"
        assert s.server.port == 5000
        assert s.sda.path == ""

    def test_load_client_config_from_file(self, monkeypatch):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write("[Settings]\nserver_ip = 10.20.30.40\nport = 9999\n")
            f.flush()
            s = Settings.load_client_config(config_path=f.name)

        os.unlink(f.name)
        assert s.server.ip == "10.20.30.40"
        assert s.server.port == 9999

    def test_load_client_config_missing_file(self, monkeypatch):
        s = Settings.load_client_config(config_path="nonexistent.ini")
        assert s.server.ip == "192.168.88.205"
        assert s.server.port == 5000

    def test_load_server_config_from_file(self, monkeypatch):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write('[SDA]\npath_to_SDA = "C:\\path\\to\\sda.exe"\n')
            f.flush()
            s = Settings.load_server_config(config_path=f.name)

        os.unlink(f.name)
        assert "sda.exe" in s.sda.path

    def test_load_server_config_missing_file(self, monkeypatch):
        s = Settings.load_server_config(config_path="nonexistent.ini")
        assert s.sda.path == ""

    def test_captcha_key_from_env(self, monkeypatch):
        monkeypatch.setenv("CAPTCHA_KEY", "key123")
        s = Settings()
        assert s.captcha_key == "key123"
