import os
from utils.channel_parser import ChannelParser

channels_to_parse = ['vietnamnews_ru']

for channel in channels_to_parse:
    parser = ChannelParser(channel, '2025-04-12 00:00:00', None)
    parser.scrape()

    path_to_save = os.path.abspath(f'./data/{channel}.json')
    path_to_save = os.path.abspath('C:/Users/User/IdeaProjects/python/channel.json')
    parser.save_json(path_to_save)



