import os
import json
import argparse
from utils.telegram_parser import TelegramPrivateChannelParser

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

        response = {
            "success": True,
            "error": None
        }

        if result:
            tg_parser.save(output_file)
            response.update({
                "found_messages": True,
                "file_path": output_file,
                "message_count": len(result),
                "status": f"Найдено {len(result)} сообщений"
            })
        else:
            response.update({
                "found_messages": False,
                "status": "Сообщения не найдены"
            })

        print(json.dumps(response, ensure_ascii=False, indent=2))

    except Exception as e:
        error_response = {
            "success": False,
            "found_messages": False,
            "error": str(e),
            "status": "Произошла ошибка"
        }
        print(json.dumps(error_response, ensure_ascii=False, indent=2))

    finally:
        tg_parser.close()

if __name__ == "__main__":
    main()
