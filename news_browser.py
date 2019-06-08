import feedparser
import os
from os.path import join, dirname
import urllib.request
import urllib.parse
import json
import pprint
import numpy as np
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
try:
    GOOGLE_SCRIPT_END_POINT = os.environ["GOOGLE_SCRIPT_END_POINT"]
except:
    pass


def create_news_list(key_word, user_id, check_duplicate_able, sent_history):
    print("check_duplicate_able is:", check_duplicate_able)
    result = search(key_word)
    r_titles = remove_blank(get_published_title(user_id))
    news = list()

    for i, entry in enumerate(result.entries, 1):
        sortkey = create_sortKey(entry)
        tmp = {
            "title": entry.title,
            "link": entry.link,
            "published": entry.published,
            "sortkey": sortkey
        }

        result_is_published = is_published(tmp, r_titles)
        if result_is_published and check_duplicate_able:
            print("%s has published" % tmp['title'])
            continue
        news.append(tmp)
        if len(news) >= 3: break

    news = sorted(news, key=lambda x: x['sortkey'])
    sent_hash_to_google(filter_published_news(news, r_titles), user_id, sent_history)
    return news


def filter_published_news(news, r_titles):
    sending_link = list()
    [sending_link.append(i['link']) for i in news[:3] if not is_published(i, r_titles)]
    return sending_link


def search(key_word):
    query = urllib.parse.quote(key_word)
    url = "https://news.google.com/news/rss/search/section/q/%s/%s?ned=jp&amp;hl=ja&amp;gl=JP" % (
        query, query)
    return feedparser.parse(url)


def create_sortKey(entry):
    p = entry.published_parsed
    return "%04d%02d%02d%02d%02d%02d" % (p.tm_year, p.tm_mon, p.tm_mday,
                                            p.tm_hour, p.tm_min, p.tm_sec)


def search_news(key_word, user_id, check_duplicate_able=False, sent_history=True):
    search_result = create_news_list(key_word, user_id, check_duplicate_able, sent_history)
    print("search result: ", search_result)
    messages = [
        "%s\n%s " % (message['link'], message['title'])
        for message in search_result[:3]
    ]
    print("messages: ", messages)
    return messages


def is_published(tmp, result):
    for title in result:
        if title == (tmp['link']):
            return True
    else:
        return False


def get_published_title(user_id):
    param = {'type': "get_title", 'user_id': user_id}
    req = urllib.request.Request(
        '{}?{}'.format(GOOGLE_SCRIPT_END_POINT, urllib.parse.urlencode(param)))
    with urllib.request.urlopen(req) as res:
        response = res.read()
    return np.array(json.loads(response)['data']).reshape(-1)


def sent_hash_to_google(news, user_id, sent_history):
    print("sent history", sent_history)
    if not sent_history: return
    print("history sending...")
    param = {'type': "set_title", 'user_id': user_id, 'titles': news}
    req = urllib.request.Request(GOOGLE_SCRIPT_END_POINT,
                                 json.dumps(param).encode(),
                                 {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as res:
        body = res.read()
        pprint.pprint(body.decode())


def remove_blank(array):
    u_arr = np.unique(array)
    return np.delete(u_arr, 0)


if __name__ == '__main__':
    create_news_list(
        "テスト", "U542cfb0a136e0243dab8582e661e0028", check_duplicate_able=True)
