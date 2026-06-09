import hmac


def is_authorized(provided: str, expected: str) -> bool:
    """Проверка токена доступа.

    Если ``expected`` пустой — аутентификация отключена (разрешаем всё, но
    вызывающий код должен залогировать предупреждение). Сравнение через
    ``hmac.compare_digest`` для защиты от timing-атак.
    """
    if not expected:
        return True
    if not provided:
        return False
    return hmac.compare_digest(provided, expected)
