# SteamAutoLogin V2.0

Windows-приложение клиент-сервер для автоматического входа в Steam в локальной
сети. Клиенты берут свободные аккаунты из MySQL, запускают Steam и обрабатывают
двухфакторную аутентификацию (Steam Guard) через центральный сервер со
Steam Desktop Authenticator (SDA).

## Архитектура

```
shared/   — общий код (config, db, protocol, auth, logger, exceptions)
client/   — запускается на рабочих ПК
server/   — запускается на центральной машине
```

- `client/main.py` — точка входа клиента (принимает appid игры как аргумент)
- `server/main.py` — точка входа сервера (TCP-сокет сервер)
- Протокол: JSON поверх TCP с length-prefixed framing
- Конфигурация: `.env` для секретов, INI-файлы для путей и адресов

### Модули

**shared/**
- `config.py` — `Settings` (dataclass), загрузка из `.env` + INI
- `db.py` — подключение к MySQL, выборка свободных аккаунтов, смена статуса
- `protocol.py` — `Message`/`GuardResponse`, сериализация, чтение из сокета
- `auth.py` — проверка токена доступа (`hmac.compare_digest`)
- `netutil.py` — определение локального IP
- `logger.py` — настройка loguru + уведомления в Telegram
- `exceptions.py` — доменные исключения

**client/**
- `main.py` — оркестрация: argparse → БД → Steam → блокировка ввода
- `network.py` — TCP-клиент (ping, запрос guard)
- `steam_automation.py` — автоматизация окна Steam (pywinauto)
- `input_guard.py` — блокировка клавиатуры/мыши на время входа (pynput)
- `gui.py` — окно выбора аккаунта (customtkinter)

**server/**
- `main.py` — запуск сервера и инициализация компонентов
- `network.py` — TCP accept/send
- `handlers.py` — роутинг сообщений (guard/ping) + проверка токена
- `sda_automation.py` — автоматизация SDA (pywinauto)
- `account_manager.py` — статусы аккаунтов + `backup.json`

## Требования окружения

- **MySQL** с базой `accounts` и таблицей `users`
  (колонки: `id`, `login_steam`, `pass_steam`, `auth_mail`, `game`, `online`, `active`)
- **Steam** установлен и зарегистрирован в реестре `HKCU\Software\Valve\Steam`
- **Steam Desktop Authenticator** установлен; путь указан в `server/config_sda.ini`
- Интерфейс Steam на **русском языке** (проверки заголовков окон используют русские строки)
- Файл `.env` в корне проекта (см. `.env.example`)

## Установка

```powershell
pip install -r requirements.txt
```

## Конфигурация

```powershell
copy .env.example .env   # заполнить секреты, в т.ч. AUTH_TOKEN
```

- `client/config.ini` — IP и порт сервера
- `server/config_sda.ini` — путь к SDA

## Запуск

```powershell
python -m server          # на центральной машине
python -m client 730      # на рабочем ПК (730 — appid игры, напр. CS2)
```

## Безопасность

- Секреты хранятся в `.env` (gitignored), не в коде. См. `.env.example`.
- `AUTH_TOKEN` — общий секрет сервера и клиентов. Сервер выдаёт коды Steam Guard
  только запросам с верным токеном; пустой токен отключает проверку (с
  предупреждением в логе). Значение должно совпадать на всех машинах.
- Протокол — JSON поверх TCP с length-prefixed framing.

## Особенности

- Все строки интерфейса и логов — на русском языке.
- `pywinauto` с `backend="uia"` для автоматизации окон.
- `pynput` блокирует клавиатуру и мышь во время входа; авто-разблокировка через 30 секунд.

## Разработка

```powershell
ruff check .          # линтинг
mypy shared server    # проверка типов
pytest -q             # тесты
```

CI (GitHub Actions) прогоняет ruff + mypy + pytest на Python 3.10–3.12.
