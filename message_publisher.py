import os
from os.path import join, dirname
import json
import urllib.request
import numpy as np
import collections
from dotenv import load_dotenv
from linebot.models import TextSendMessage
from linebot import LineBotApi

import news_browser

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
GOOGLE_SCRIPT_END_POINT = os.environ["GOOGLE_SCRIPT_END_POINT"]


class MessagePublisher:
    def __init__(self, gas_end_point, header, line_bot_api):
        self.gas_end_point = gas_end_point
        self.header = header
        self.line_bot_api = line_bot_api

    def publish(self):
        self.get_user_list()
        for user in self.user_list:
            key_word_for_search = self.__get_key_word(user)
            news = news_browser.search_news(
                key_word_for_search,
                user,
                check_duplicate_able=True,
                sent_history=False)
            sending_data = [
                TextSendMessage(
                    text='本日のNEWS配信(%sさんのHOT WORDは「%s」です)' %
                    (self.line_bot_api.get_profile(user).display_name,
                     key_word_for_search))
            ]
            for m in news:
                sending_data.append(TextSendMessage(text=m))
            self.line_bot_api.push_message(user, sending_data)

    def publish_test(self):
        self_id = os.environ['SELF_ID']
        key_word_for_search = self.__get_key_word(self_id)
        news = news_browser.search_news(
            key_word_for_search,
            self_id,
            check_duplicate_able=True,
            sent_history=True)
        print("publish news is: ", news)
        print(list(self.remove_title(news)))

    def publish_by_manual(self, message):
        self.get_user_list()
        for user in self.user_list:
            self.line_bot_api.push_message(user, TextSendMessage(text=message))

    def get_user_list(self):
        param = {'type': 'get_id'}
        req = urllib.request.Request('{}?{}'.format(
            self.gas_end_point, urllib.parse.urlencode(param)))
        with urllib.request.urlopen(req) as res:
            response = res.read()
        user_list = np.array(json.loads(response)['data']).reshape(-1)
        self.user_list = user_list

    def __get_key_word(self, user_id):
        param = {'type': 'get_word', 'user_id': user_id}
        req = urllib.request.Request('{}?{}'.format(
            self.gas_end_point, urllib.parse.urlencode(param)))
        with urllib.request.urlopen(req) as res:
            response = res.read()
        print("res: ", response.decode())
        key_words = np.array(json.loads(response)['data']).reshape(-1)
        count = collections.Counter(key_words).most_common(3)
        print(count)
        key_word = self.__remove_blank(count)
        print("use key word is: %s" % key_word)
        return key_word

    def __remove_blank(self, tuple):
        # need to check blank test additionally
        if tuple[0][0] == '' or tuple[0][0] == ' ':
            if tuple[1][0] == '' or tuple[1][0] == ' ':
                return tuple[2][0]
            return tuple[1][0]
        return tuple[0][0]

    def remove_title(self, news):
        for l in news:
            yield l.split("\n")[0]


if __name__ == '__main__':
    headers = {'Content-Type': 'application/json'}
    message_publisher = MessagePublisher(GOOGLE_SCRIPT_END_POINT, headers,
                                         line_bot_api)
    message_publisher.publish_test()
