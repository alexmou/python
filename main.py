import os
from utils.channel_parser import ChannelParser

channels_to_parse = ['vietnamnews_ru']

for channel in channels_to_parse:
    parser = ChannelParser(channel, '2025-04-13 00:00:00', None)
    parser.scrape()

    os.makedirs('./data', exist_ok=True)
    path_to_save = os.path.abspath(f'./data/{channel}.json')

    # Получаем JSON строку и выводим
    json_result = parser.save_json(path_to_save)
    print(json_result)