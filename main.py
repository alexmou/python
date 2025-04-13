import os
import argparse
from utils.channel_parser import ChannelParser

def main():
    # Настройка парсера аргументов командной строки
    parser = argparse.ArgumentParser(description='Telegram Channel Parser')
    parser.add_argument('--channels', nargs='+', required=True,
                        help='List of channels to parse (e.g., vietnamnews_ru channel2)')
    parser.add_argument('--start_date', required=True,
                        help='Start date in format YYYY-MM-DD or YYYY-MM-DD HH:MM:SS')
    parser.add_argument('--finish_date', default=None,
                        help='Optional finish date in same format')

    args = parser.parse_args()

    for channel in args.channels:
        print(f"\nParsing channel: {channel}")
        parser = ChannelParser(
            channel_name=channel,
            start_date=args.start_date,
            finish_date=args.finish_date
        )

        try:
            parser.scrape()
            os.makedirs('./data', exist_ok=True)
            path_to_save = os.path.abspath(f'./data/{channel}.json')
            result = parser.save_json(path_to_save)
            #print(f"Successfully saved to {path_to_save}")
            print(result)
        except Exception as e:
            print(f"Failed to parse {channel}: {str(e)}")

if __name__ == "__main__":
    main()