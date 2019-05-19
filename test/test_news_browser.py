import sys
import os

sys.path.append(os.getcwd())
import news_browser


def test_filter_published_news():
    print("testtesttest")
    test_case = {
        'news': [{'link': 'https://news.tbs.co.jp/newseye/tbs_newseye3677003.html'},
                  {'link': 'https://www.kobe-np.co.jp/news/sports/201905/0012344139.shtml'},
                  {'link': 'https://www.nikkansports.com/sports/athletics/news/201905190000154.html'}],
        'r_titles': ['https://www.nikkansports.com/sports/athletics/news/201905190000154.html']
    }
    expected = ['https://news.tbs.co.jp/newseye/tbs_newseye3677003.html', 'https://www.kobe-np.co.jp/news/sports/201905/0012344139.shtml']
    assert(expected == news_browser.filter_published_news(test_case['news'], test_case['r_titles']))
