import os
from utils.channel_parser import ChannelParser

channels_to_parse = ['vietnamnews_ru', '', '']

for channel in channels_to_parse:
    parser = ChannelParser(channel, '2025-04-08 00:00:00', '2025-04-09 00:00:00')
    parser.scrape()

    path_to_save = os.path.abspath(f'./data/{channel}.json')
    parser.save_json(path_to_save)



