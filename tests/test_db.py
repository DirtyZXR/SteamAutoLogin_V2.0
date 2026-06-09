import pytest

from shared.db import _safe_table


class TestSafeTable:
    def test_valid_identifiers(self):
        assert _safe_table("users") == "users"
        assert _safe_table("user_accounts") == "user_accounts"
        assert _safe_table("_tbl1") == "_tbl1"

    @pytest.mark.parametrize(
        "bad",
        ["users; DROP TABLE x", "1users", "user-table", "tbl name", "", "users--"],
    )
    def test_rejects_injection_and_invalid(self, bad):
        with pytest.raises(ValueError):
            _safe_table(bad)
