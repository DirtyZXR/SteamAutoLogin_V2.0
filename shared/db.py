import mysql.connector
from loguru import logger

from shared.config import DatabaseConfig


def create_connection(db_config: DatabaseConfig):
    try:
        connection = mysql.connector.connect(
            host=db_config.host,
            user=db_config.user,
            passwd=db_config.password,
            database=db_config.name,
        )
        return connection
    except mysql.connector.Error as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        return None


def set_account_online(db_config: DatabaseConfig, account_id: int, online: bool) -> bool:
    query = "UPDATE users SET online = %s WHERE id = %s"
    status_str = "online" if online else "offline"
    try:
        connection = create_connection(db_config)
        if connection is None:
            return False
        cursor = connection.cursor()
        cursor.execute(query, (online, account_id))
        connection.commit()
        cursor.close()
        connection.close()
        logger.info(f"Аккаунт {account_id} -> {status_str}")
        return True
    except mysql.connector.Error:
        logger.error(f"Не удалось обновить статус аккаунта {account_id}")
        return False


def get_free_accounts(db_config: DatabaseConfig, appid: str) -> list[tuple]:
    query = """
        SELECT id, login_steam, pass_steam, auth_mail, game
        FROM users
        WHERE online = FALSE AND active = TRUE
    """
    try:
        connection = create_connection(db_config)
        if connection is None:
            return []
        with connection.cursor() as cursor:
            cursor.execute(query)
            accounts = cursor.fetchall()
        connection.close()

        filtered = []
        for account in accounts:
            appids = account[-1].split("-")
            if appid in appids:
                filtered.append(account)
        return filtered
    except mysql.connector.Error:
        logger.error("Ошибка при получении аккаунтов из БД")
        return []
