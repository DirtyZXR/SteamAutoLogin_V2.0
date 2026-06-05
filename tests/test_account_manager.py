import json
import os
from pathlib import Path
from unittest.mock import patch

from server.account_manager import BACKUP_FILE, AccountManager
from shared.config import DatabaseConfig


class TestAccountManager:
    def setup_method(self):
        if Path(BACKUP_FILE).exists():
            os.unlink(BACKUP_FILE)

    def teardown_method(self):
        if Path(BACKUP_FILE).exists():
            os.unlink(BACKUP_FILE)

    def _make_manager(self) -> AccountManager:
        db_config = DatabaseConfig(host="localhost", user="u", password="p", name="test")
        return AccountManager(db_config)

    def test_load_backup_creates_file_if_missing(self):
        mgr = self._make_manager()
        assert Path(BACKUP_FILE).exists()
        assert mgr.backup == {}

    def test_load_backup_reads_existing(self):
        with open(BACKUP_FILE, "w") as f:
            json.dump({"5": 1, "10": 0}, f)

        mgr = self._make_manager()
        assert mgr.backup == {"5": 1, "10": 0}

    def test_load_backup_handles_corrupt_file(self):
        with open(BACKUP_FILE, "w") as f:
            f.write("not json{{{")

        mgr = self._make_manager()
        assert mgr.backup == {}

    @patch("server.account_manager.set_account_online")
    def test_mark_online_new_account(self, mock_set_online):
        mock_set_online.return_value = True
        mgr = self._make_manager()

        mgr.mark_online("42")
        assert mgr.backup["42"] == 1
        mock_set_online.assert_called_once()

    def test_mark_online_existing_account(self):
        mgr = self._make_manager()
        mgr.backup = {"7": 0}

        mgr.mark_online("7")
        assert mgr.backup["7"] == 1

    @patch("server.account_manager.set_account_online")
    def test_check_offline_cycle_marks_zero_as_offline(self, mock_set_online):
        mock_set_online.return_value = True
        mgr = self._make_manager()
        mgr.backup = {"3": 0, "8": 1}

        mgr.check_offline_cycle()

        assert "3" not in mgr.backup
        assert mgr.backup["8"] == 0
        mock_set_online.assert_called_once()

    def test_check_offline_cycle_resets_active_to_zero(self):
        mgr = self._make_manager()
        mgr.backup = {"1": 1, "2": 1}

        with patch("server.account_manager.set_account_online"):
            mgr.check_offline_cycle()

        assert mgr.backup["1"] == 0
        assert mgr.backup["2"] == 0

    def test_backup_saved_after_mark_online(self):
        mgr = self._make_manager()
        with patch("server.account_manager.set_account_online", return_value=True):
            mgr.mark_online("99")

        with open(BACKUP_FILE) as f:
            saved = json.load(f)
        assert saved["99"] == 1

    def test_mark_online_converts_to_string(self):
        mgr = self._make_manager()
        with patch("server.account_manager.set_account_online", return_value=True):
            mgr.mark_online(15)
        assert "15" in mgr.backup
