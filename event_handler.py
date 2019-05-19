import os
from os.path import join, dirname
import urllib.request
import json
import pprint
from dotenv import load_dotenv

from event_proseccor import EventProcessor
from message_publisher import MessagePublisher
from rich_menu import RichMenu, RichMenuManager

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, FollowEvent, UnfollowEvent)

app = Flask(__name__)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
GOOGLE_SCRIPT_END_POINT = os.environ["GOOGLE_SCRIPT_END_POINT"]
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
processor = EventProcessor(line_bot_api)


@app.route("/callback", methods=['POST'])
def callback():
    print("catch event: ", request.get_data(as_text=True))
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@app.route('/push', methods=['GET'])
def send_push_message():
    headers = {'Content-Type': 'application/json'}
    message_publisher = MessagePublisher(
        GOOGLE_SCRIPT_END_POINT, headers, line_bot_api)
    message_publisher.publish()
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def response_message(event):
    print("catch message: ", event)
    if event.message.text == "設定":
        print("call config")
    else:
        processor.response_message(event)


# register to spreed sheet through GAS
@handler.add(FollowEvent)
def add_new_user(event):
    print("catch new follower: ", event)
    processor.add_new_user(event)


# remove user by blocking through GAS
@handler.add(UnfollowEvent)
def remove_blocking_user(event):
    print("catch remove follower: ", event)
    un_follow_event = {'user_id': event.source.user_id, 'type': 'unfollow'}
    headers = {'Content-Type': 'application/json'}
    param = json.dumps(un_follow_event)
    req = urllib.request.Request(GOOGLE_SCRIPT_END_POINT, param.encode(),
                                 headers)
    print("sending param: ", param)
    with urllib.request.urlopen(req) as res:
        body = res.read()
        pprint.pprint(body.decode())


def add_rm_all_user():
    rmm = RichMenuManager(LINE_CHANNEL_ACCESS_TOKEN)
    rm = RichMenu(name="Test menu", chat_bar_text="Open this menu")
    rm.add_area(0, 0, 1250, 843, "message", "テキストメッセージ")
    rm.add_area(1250, 0, 1250, 843, "message", "help")
    res = rmm.register(rm, (os.getcwd() + "/image/controller_01.png"))
    richmenu_id = res["richMenuId"]
    print("Registered as " + richmenu_id)
    message_publisher = MessagePublisher(
        GOOGLE_SCRIPT_END_POINT, {'Content-Type': 'application/json'}, line_bot_api)
    users = message_publisher.get_user_list()
    for user_id in users:
        rmm.apply(user_id, richmenu_id)
        res2 = rmm.get_applied_menu(user_id)
        print(user_id + ":" + res2["richMenuId"])


def remove_rm():
    rmm = RichMenuManager(LINE_CHANNEL_ACCESS_TOKEN)
    rmm.remove_all()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
