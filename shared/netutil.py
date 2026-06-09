import socket

from loguru import logger


def get_local_ip(fallback: str = "127.0.0.1") -> str:
    """Определить локальный IP машины через исходящий UDP-сокет.

    Реального соединения с 8.8.8.8 не происходит (UDP без отправки данных),
    нужен только для выбора сетевого интерфейса ОС.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except OSError:
        logger.warning("Не удалось определить локальный IP, использую {fb}", fb=fallback)
        ip = fallback
    finally:
        s.close()
    logger.info("Определён локальный IP: {ip}", ip=ip)
    return ip
