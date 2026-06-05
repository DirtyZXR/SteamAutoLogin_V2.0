from loguru import logger


def setup_logger(log_file: str, telegram_params: dict | None = None, level: str = "INFO"):
    logger.add(
        log_file,
        format="{time:DD.MM.YYYY at HH:mm:ss} | {name}:{function}:{line} | {level} | {message}",
        level=level,
        rotation="100MB",
    )
    if telegram_params and telegram_params.get("token"):
        from notifiers.logging import NotificationHandler

        handler = NotificationHandler("telegram", defaults=telegram_params)
        logger.add(handler, level="ERROR")
