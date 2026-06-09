from shared.auth import is_authorized


class TestIsAuthorized:
    def test_disabled_when_expected_empty(self):
        # Пустой ожидаемый токен = аутентификация отключена.
        assert is_authorized("", "") is True
        assert is_authorized("anything", "") is True

    def test_matching_token(self):
        assert is_authorized("secret-123", "secret-123") is True

    def test_wrong_token(self):
        assert is_authorized("wrong", "secret-123") is False

    def test_empty_provided_when_expected_set(self):
        assert is_authorized("", "secret-123") is False
