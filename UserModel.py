import datetime

from bs4 import BeautifulSoup

import Main
from ZhihuLogin import *

'''
******未完成*****
info:用户爬取与解析

'''
flag = True


class User(object):
    # 连接数据库
    con = db.DbUtil.connect()
    # 请求暂存，知乎限制连续访问
    next_urls = []
    # 新用户
    new_url_tokens = set()
    # 已访问用户
    old_url_tokens = set()
    # 已保存用户
    saved_users_set = set()

    URL_TEMPLATE = "https://www.zhihu.com/api/v4/members/{0}/followees?"
    QUERY_PARAMS = "include=data%5B%2A%5D.answer_count%2Carticles_count%2Cgender%2Cfollower_count%2Cis_followed%2Cis_following%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit=20&offset={0}"

    def __init__(self, account, domin):
        self.session = account.session
        self.domin = domin

    # 下载其他用户的url_token
    def download(self, url):
        if url is None:
            return None
        response = self.session.get(url)
        self.session.cookies.save()
        if response.status_code == 200:
            return response.text
        else:
            raise Exception('线程 %s 下载url：%s 失败 响应状态码 %s' % (threading.current_thread().name, url, response.status_code))

    def parse(self, response):
        try:
            # print(response)
            json_body = json.loads(response)
            json_data = json_body['data']
            for item in json_data:
                # 判断token是否已经请求，防止重复请求
                if not User.old_url_tokens.__contains__(item['url_token']):
                    if User.new_url_tokens.__len__() < 2000:
                        User.new_url_tokens.add(item['url_token'])
                if not User.saved_users_set.__contains__(item['url_token']):
                    # https://www.zhihu.com/people/guo-jia-32/logs
                    user_logs = self.get_user_logs(item['url_token'])
                    try:
                        Main.user_lock.acquire()
                        print('%s 正在保存用户 %s' % (threading.current_thread().name, item['name']))
                        dictMerge = dict(item, **user_logs)
                        self.save(dictMerge)
                        Main.user_lock.release()
                    except Exception as e:
                        Main.x_lock.acquire()
                        with open('./log.txt', 'a', encoding='utf-8') as f:
                            f.write(
                                threading.current_thread().name + str(e.args) + str(datetime.datetime.now()) + '\r\n')
                        print('%s 保存用户 %s 失败: %s' % (threading.current_thread().name, item['name'], e.args))
                        Main.user_lock.release()
                        Main.x_lock.release()
                    User.saved_users_set.add(item['url_token'])

            if not json_body['paging']['is_end']:
                # 若关注用户数为请求完毕，暂存现场
                next_url = json_body['paging']['next']
                token_tuple = re.findall('members/(.*?)/followees.*?offset=(.*?)$', next_url, re.S)
                User.next_urls.append(token_tuple[0])
                # 知乎限制连续访问同一个用户的关注列表
                # response2 = self.download(next_url)
                # self.parse(response2)
            else:
                pass
        except Exception as e:
            raise Exception('thread %s parse userlist error %s' % (threading.current_thread().name, e.args))

    def get_user_logs(self, token):
        url = 'https://www.zhihu.com/people/{0}'.format(token)
        if url is None:
            return None
        response = self.session.get(url)
        self.session.cookies.save()
        if response.status_code == 200:
            return response.text
        raise Exception('线程 %s 下载用户log：%s 失败 响应状态码 %s' % (threading.current_thread().name, url, response.status_code))


    def parse_logs(self, text):
        soup = BeautifulSoup(text, 'lxml')
        infos = {}
        # 赞同数
        infos['agree'] = soup.select('span.Tabs-meta')[0].text
        # 感谢数
        infos['thanks'] = soup.select('span.zm-profile-header-user-thanks strong')[0].text
        # 提问 回答 文章 收藏 公共编辑
        lists = soup.select('.num')
        infos['asks'] = lists[0].text
        infos['collections'] = lists[3].text
        infos['logs'] = lists[4].text
        return infos

    # def parse_home(self, text):
    #     soup = BeautifulSoup(text, 'lxml')
    #     infos = {}
    #     # 回答 提问 文章 专栏 想法
    #     soup.select('span.Tabs-meta')
    #     # 成就信息
    #     achievements = soup.select('.Profile-sideColumn .card')
    #     if achievements.__len__()>0:
    #         pass
    #     else:
    #         infos['achievement'] = None
    #     # 提问 回答 文章 收藏 公共编辑
    #     lists = soup.select('.num')
    #     infos['asks'] = lists[0].text
    #     infos['collections'] = lists[3].text
    #     infos['logs'] = lists[4].text
    #     return infos

    def get_new_url(self):
        global flag
        if User.new_url_tokens.__len__() > 0 and flag == True:
            flag = False
            token = User.new_url_tokens.pop()
            User.old_url_tokens.add(token)
            url = User.URL_TEMPLATE.format(token) + User.QUERY_PARAMS.format('0')
        elif User.next_urls.__len__() > 0:
            flag = True
            token_offset = User.next_urls.pop(0)
            url = User.URL_TEMPLATE.format(token_offset[0]) + User.QUERY_PARAMS.format(token_offset[1])
        else:
            return None
        # print(url)
        return url

    # 保存数据库
    def save(self, data):
        cur = User.con.cursor()
        if len(data['badge']) > 0:
            data['badge'] = str(data['badge'])

        sql = "REPLACE into user values ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', " \
              "'{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
            data['id'], data['agree'], data['thanks'], data['asks'], data['answer_count'], data['articles_count'],
            data['collections'], data['logs'],
            data['badge'], data['follower_count'], data['gender'], data['headline'], data['is_advertiser'],
            data['is_org'], data['name'], data['type'], data['url'], data['url_token'],
            data['user_type'], datetime.datetime.now())
        # print(sql)
        cur.execute(sql)
        User.con.commit()
        cur.close()

    # 关闭数据库连接
    def close(self):
        User.con.close()
