import datetime

from bs4 import BeautifulSoup
import requests

import TopicModel
from ZhihuLogin import *

'''
******未完成*****
info:用户爬取与解析

'''


class User2(object):
    # 连接数据库
    con = db.DbUtil.connect()
    new_url_tokens = set()
    old_url_tokens = set()
    saved_users_set = set()

    urls = ['https://www.zhihu.com/api/v4/members/xiaozhenliu/followees?include=data%5B%2A%5D.answer_count%2Carticles_count%2Cgender%2Cfollower_count%2Cis_followed%2Cis_following%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit=20&offset=0',
            'https://www.zhihu.com/api/v4/members/alexandeng/followees?include=data%5B%2A%5D.answer_count%2Carticles_count%2Cgender%2Cfollower_count%2Cis_followed%2Cis_following%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit=20&offset=0',
            'https://www.zhihu.com/api/v4/members/xiaozhenliu/followees?include=data%5B%2A%5D.answer_count%2Carticles_count%2Cgender%2Cfollower_count%2Cis_followed%2Cis_following%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit=20&offset=20']
    URL_TEMPLATE = "https://www.zhihu.com/api/v4/members/{0}/followees?"
    QUERY_PARAMS = "include=data%5B%2A%5D.answer_count%2Carticles_count%2Cgender%2Cfollower_count%2Cis_followed%2Cis_following%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit=20&offset=0"

    def __init__(self, account, domin):
        self.session = account.session
        self.domin = domin

    # 下载其他用户的url_token
    def download(self, url):
        if url is None:
            return None
        try:
            response = self.session.get(url)
            self.session.cookies.save()
            if response.status_code == 200:
                return response.text
            return None
        except:
            return None

    def parse(self, response):
        try:
            print(response)
            json_body = json.loads(response)
            json_data = json_body['data']

        except Exception as e:
            with open('./log.txt', 'a', encoding='utf-8') as f:
                f.write(str(e.args) + str(datetime.datetime.now()) + '\r\n')
            print('user parse error: %s' % (e.args,))

    def get_new_url(self):
        # url_token = User2.new_url_tokens.pop()
        # User2.old_url_tokens.add(url_token)
        # url = User2.URL_TEMPLATE.format(url_token) + User2.QUERY_PARAMS
        # print(url)
        return User2.urls.pop(0)

    # 保存数据库
    def save(self, data):
        cur = User2.con.cursor()
        if len(data['badge']) > 0:
            data['badge'] = json.dumps(data['badge'])

        sql = "insert into user values ('{}' ,'{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(
            data['id'], data['answer_count'], data['articles_count'],
            data['badge'], data['follower_count'], data['gender'], data['headline'], data['is_advertiser'],
            data['is_org'], data['name'], data['type'], data['url'], data['url_token'],
            data['user_type'])
        # print(sql)
        cur.execute(sql)
        User2.con.commit()
        cur.close()

    # 关闭数据库连接
    def close(self):
        User2.con.close()
