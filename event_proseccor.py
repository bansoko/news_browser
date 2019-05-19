import os
import urllib
import pprint
import json

import news_browser

from linebot.models import (
    TextSendMessage, FollowEvent)

GOOGLE_SCRIPT_END_POINT = os.environ["GOOGLE_SCRIPT_END_POINT"]


class EventProcessor:
    def __init__(self, line_bot_api):
        self.google_end_point = GOOGLE_SCRIPT_END_POINT
        self.line_bot_api = line_bot_api

    def response_message(self, event):
        try:
            results = news_browser.search_news(event.message.text, event.source.user_id)
            sending_data = list()
            for message in results:
                sending_data.append(TextSendMessage(text=message))
            print("sending data: ", sending_data)

            param = {'type': "set",
                     'user_id': event.source.user_id,
                     'key_word': self.__split_key_word(event.message.text)}
            req = urllib.request.Request(
                GOOGLE_SCRIPT_END_POINT, json.dumps(param).encode(),
                {'Content-Type': 'application/json'})
            with urllib.request.urlopen(req) as res:
                body = res.read()
                pprint.pprint(body.decode())

            self.line_bot_api.reply_message(event.reply_token, sending_data)
        except BaseException:
            self.line_bot_api.reply_message(
                event.reply_token, TextSendMessage(
                    text='不具合につき調整中です'))

    def add_new_user(self, event):
        events = JsonEncoder().encode(event)
        headers = {'Content-Type': 'application/json'}

        profile = self.line_bot_api.get_profile(event.source.user_id)

        parsed_event = json.loads(events)
        parsed_event['user_id'] = event.source.user_id
        parsed_event['user_name'] = profile.display_name
        dump_event = json.dumps(parsed_event)

        req = urllib.request.Request(
            GOOGLE_SCRIPT_END_POINT,
            dump_event.encode(),
            headers)
        print("parse events: ", dump_event)
        with urllib.request.urlopen(req) as res:
            body = res.read()
            pprint.pprint(body.decode())

    def __split_key_word(self, text):
        return text.split(" ")


class JsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, FollowEvent):
            return o.__dict__

