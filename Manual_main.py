import os
import argparse
from telegram_parser import TelegramPrivateChannelParser

def main():
    parser = argparse.ArgumentParser(description="Telegram Private Channel Parser")
    parser.add_argument("channel", help="Название канала (без @)")
    args = parser.parse_args()

    channel = args.channel

    # Универсальные пути (работают на Linux/Windows)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    session_dir = os.path.join(base_dir, "cookies")
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(session_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    timestamp_file = os.path.join(data_dir, "timestamps.json")
    output_file = os.path.join(data_dir, f"{channel}.json")

    tg_parser = TelegramPrivateChannelParser(
        channel_name=channel,
        session_dir=session_dir,
        timestamp_file=timestamp_file
    )

    try:
        result = tg_parser.scrape()

        if result:
            tg_parser.save(output_file)
            print(f"✅ Сохранено: {output_file}")
            print(f"🔍 Найдено сообщений: {len(result)}")
        else:
            print("⚠️ Сообщения не найдены или произошла ошибка.")
    except Exception as e:
        print(f"🔥 Критическая ошибка: {str(e)}")
    finally:
        tg_parser.close()

if __name__ == "__main__":
    main()
