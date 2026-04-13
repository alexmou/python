# Telegram Private Channel Parser

This project is designed to automatically scrape private Telegram channels from the Telegram Web interface and save new messages into a JSON file.

# Парсер приватных Telegram-каналов

Этот проект предназначен для автоматизированного сканирования приватных Telegram-каналов через веб-версию Telegram и сохранения новых сообщений в JSON-файл.

## Purpose / Назначение

The `main.py` script connects to `web.telegram.org`, opens the specified channel, and extracts new messages that were not processed before. Data is saved to the `data/` folder and timestamps are used to avoid collecting already seen messages.

Скрипт `main.py` подключается к `web.telegram.org`, загружает указанный канал и извлекает новые сообщения, которые ещё не были обработаны ранее. Данные сохраняются в папку `data/` и используются временные метки, чтобы не повторять сбор уже виденных сообщений.

## Features / Особенности

- Scrapes messages from a private Telegram channel via Telegram Web
- Saves results into JSON files
- Stores the last processed timestamp in `data/timestamps.json` for incremental collection
- Uses a local Chrome/Chromium profile in `cookies/` to preserve the Telegram session

- Парсинг сообщений из приватного канала Telegram через Web Telegram
- Сохранение результатов в JSON-файлы
- Хранение последней временной метки в `data/timestamps.json` для инкрементального сбора
- Использование локальной серии cookies/Chrome-профиля для сохранения сессии Telegram

## Requirements / Требования

- Python 3.10+ (recommended)
- Google Chrome / Chromium
- A working Telegram Web profile stored in the `cookies/` folder
- Dependencies installed from `requirements.txt`

- Python 3.10+ (рекомендуется)
- Google Chrome / Chromium
- Рабочий профиль Web Telegram в папке `cookies/`
- Установленные зависимости из `requirements.txt`

## Installation / Установка

1. Clone or move the project into your working directory.
2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Prepare the `cookies/` directory with Chrome/Chromium profile data where Telegram Web is already logged in. The project copies this profile folder and uses it to launch the browser.

1. Склонируйте или перенесите проект в рабочую папку.
2. Установите зависимости:

```bash
python -m pip install -r requirements.txt
```

3. Подготовьте директорию `cookies/` с данными профиля Chrome/Chromium, в которой уже выполнён вход в Telegram Web. По умолчанию проект копирует эту папку профиля и использует её для запуска браузера.

## Quick Start / Быстрый старт

Run only one command after installation:

```bash
python main.py nyachang_1
```

This will create `data/nyachang_1.json` and update `data/timestamps.json`.

Запустите одну команду после установки:

```bash
python main.py nyachang_1
```

Это создаст `data/nyachang_1.json` и обновит `data/timestamps.json`.

## Usage / Использование

Run the project from the repository root:

```bash
python main.py <channel_name>
```

Where `<channel_name>` is the channel name without `@`, for example:

```bash
python main.py nyachang_1
```

If you want to collect data from multiple channels, run the command for each channel one by one:

```bash
python main.py nyachang_1
python main.py another_channel
python main.py third_channel
```

After execution:

- results are saved to `data/<channel_name>.json`
- the last processed timestamp is stored in `data/timestamps.json`

Запускайте проект из корня репозитория так:

```bash
python main.py <channel_name>
```

Где `<channel_name>` — это имя канала без `@`, например:

```bash
python main.py nyachang_1
```

Если нужно собрать данные из нескольких каналов, запустите команду для каждого канала по очереди:

```bash
python main.py nyachang_1
python main.py another_channel
python main.py third_channel
```

После выполнения:

- результаты сохранятся в файл `data/<channel_name>.json`
- информация о последней обработанной метке времени запишется в `data/timestamps.json`

## Project structure / Структура проекта

- `main.py` — entry point, parses the channel argument and runs the parser
- `utils/telegram_parser.py` — scraping logic for Telegram Web
- `utils/driver_manager.py` — Selenium WebDriver setup and user profile handling
- `utils/post_parser.py` — extracts data from a single Telegram message
- `data/` — results and timestamp storage directory
- `cookies/` — local Telegram session directory

- `main.py` — точка входа, парсинг аргумента канала и управление запуском
- `utils/telegram_parser.py` — логика сбора сообщений из Telegram Web
- `utils/driver_manager.py` — настройка Selenium WebDriver и профиля пользователя
- `utils/post_parser.py` — извлечение данных из одного сообщения
- `data/` — директория для результатов и временных меток
- `cookies/` — директория для пользовательской сессии Chrome/Telegram

## Notes / Важные замечания

- If the session is not authorized, `utils/telegram_parser.py` checks for QR code and exits with an error.
- The script relies on Telegram Web DOM structure, which may change over time and require fixes.
- Output is produced in JSON format with fields like `success`, `status`, and others.

- Если сессия не авторизована, в `utils/telegram_parser.py` есть проверка QR-кода и выполнение завершится с ошибкой.
- Скрипт ориентирован на работу с веб-интерфейсом Telegram, поэтому структура DOM может измениться со временем и потребовать правок.
- Вывод выполняется в формате JSON с полем `success`, `status`, и другими полями информации о результатах.

## Example result / Пример результата

```json
{
  "success": true,
  "error": null,
  "found_messages": true,
  "file_path": "data/nyachang_1.json",
  "message_count": 12,
  "status": "Найдено 12 сообщений"
}
```
