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
    QUERY_PARAMS = "include=data%5B%2A%5D.answer_count%2Carticles_count%2Cgender%2Cfollower_count%2Cis_followed" \
                   "%2Cis_following%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit=20&offset={0}"

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
                    resp = self.get_user_home(item['url_token'])
                    user_logs = self.parse_home(resp)
                    try:
                        Main.user_lock.acquire()
                        print('%s 正在保存用户 %s' % (threading.current_thread().name, item['name']))
                        dictMerge = dict(item, **user_logs)
                        self.save(dictMerge)
                        Main.user_lock.release()
                    except Exception as e:
                        Main.x_lock.acquire()
                        with open('./logs/' + time.strftime("%Y-%m-%d", time.localtime()) + '.txt', 'a',
                                  encoding='utf-8') as f:
                            f.write(
                                threading.current_thread().name + str(e.args) + str(datetime.datetime.now()) + '\r\n')
                        # print('%s 保存用户 %s 失败: %s' % (threading.current_thread().name, item['name'], e.args))
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

    # 部分用户无法访问
    # def get_user_logs(self, token):
    #     url = 'https://www.zhihu.com/people/{0}/logs'.format(token)
    #     if url is None:
    #         return None
    #     response = self.session.get(url)
    #     self.session.cookies.save()
    #     if response.status_code == 200:
    #         return response.text
    #     raise Exception('线程 %s 下载用户log：%s 失败 响应状态码 %s' % (threading.current_thread().name, url, response.status_code))
    #
    # def parse_logs(self, text):
    #     soup = BeautifulSoup(text, 'lxml')
    #     infos = {}
    #     # 赞同数
    #     infos['agree'] = soup.select('span.zm-profile-header-user-agree strong')[0].text
    #     # 感谢数
    #     infos['thanks'] = soup.select('span.zm-profile-header-user-thanks strong')[0].text
    #     # 提问 回答 文章 收藏 公共编辑
    #     names = ['asks', 'answers', 'articles', 'collections', 'logs']
    #     lists = soup.select('.num')
    #     for i in range(0, len(lists)):
    #         infos[names[i]] = lists[i].text
    #
    #     if len(lists) < len(names):
    #         for i in range(len(lists), len(names)):
    #             infos[names[i]] = 0
    #
    #     # lists = soup.select('.num')
    #     # infos['asks'] = lists[0].text
    #     # infos['collections'] = lists[3].text
    #     # infos['logs'] = lists[4].text
    #     return infos

    def get_user_home(self, token):
        url = 'https://www.zhihu.com/people/{0}'.format(token)
        if url is None:
            return None
        response = self.session.get(url)
        self.session.cookies.save()
        if response.status_code == 200:
            return response.text
        raise Exception('线程 %s 下载用户主页：%s 失败 响应状态码 %s' % (threading.current_thread().name, url, response.status_code))

    def parse_home(self, text):
        soup = BeautifulSoup(text, 'lxml')
        # print(soup.prettify())
        infos = {}
        # 回答 提问 文章 专栏 想法 成就：收录回答 收录文章 赞同 感谢 收藏 专业认可 公共编辑
        names = ['answers', 'asks', 'posts', 'columns', 'pins', 'incAnswers', 'incPosts', 'agrees', 'thanks',
                 'collections', 'renke', 'logs']

        # 回答 提问 文章 专栏 [想法]  re.S 整体匹配
        lists = soup.select('a.Tabs-link')
        infos['answers'] = re.findall(r'/answers.*?<span class="Tabs-meta">([\d,]+)</span>', str(lists),
                                      re.S)
        infos['asks'] = re.findall(r'/asks.*?<span class="Tabs-meta">([\d,]+)</span>', str(lists), re.S)
        infos['posts'] = re.findall(r'/posts.*?<span class="Tabs-meta">([\d,]+)</span>', str(lists), re.S)
        infos['columns'] = re.findall(r'/columns.*?<span class="Tabs-meta">([\d,]+)</span>', str(lists),
                                      re.S)
        infos['pins'] = re.findall(r'/pins.*?<span class="Tabs-meta">([\d,]+)</span>', str(lists), re.S)

        # 知乎收录
        included = soup.find("svg", class_="Icon IconGraf-icon Icon--marked")
        if included is not None:
            alist = included.parent.next_sibling.find_all("a")
            infos['incAnswers'] = re.findall(r'answers/included"> ([\d,]+) 个回答', str(alist), re.S)
            infos['incPosts'] = re.findall(r'posts/included"> ([\d,]+) 篇文章', str(alist), re.S)
        # 赞同
        agree = soup.find("svg", class_="Icon IconGraf-icon Icon--like")
        if agree is not None:
            infos['agrees'] = str(agree.parent.next_sibling.next_sibling.next_sibling).replace(',', '')
        # 感谢 收藏 专业认可
        like = soup.find("svg", class_="Icon IconGraf-icon Icon--like")
        if like is not None:
            th = like.parent.parent.next_sibling.text
            infos['thanks'] = re.findall(r'([\d,]+) 次感谢', th, re.S)
            infos['collections'] = re.findall(r'([\d,]+) 次收藏', th, re.S)
            infos['renke'] = re.findall(r'([\d,]+) 次专业认可', th, re.S)
        # 公共编辑
        logs = soup.find("svg", class_="Icon IconGraf-icon Icon--commonEdit")
        if logs is not None:
            # log = logs.parent.next_sibling.text
            infos['logs'] = re.findall(r'([\d,]+) 次公共编辑', logs.parent.next_sibling.text, re.S)

        # 格式化
        for item in names:
            if item in infos and infos[item].__len__() > 0:
                infos[item] = infos[item][0].replace(',', '')
            else:
                infos[item] = '0'
        # print(infos)
        return infos

    def get_new_url(self):
        global flag
        try:
            if User.new_url_tokens.__len__() <= 0:
                flag = True
            if User.next_urls.__len__() > 0 and flag == True:
                token_offset = User.next_urls.pop(0)
                url = User.URL_TEMPLATE.format(token_offset[0]) + User.QUERY_PARAMS.format(token_offset[1])
            elif User.new_url_tokens.__len__() > 0:
                token = User.new_url_tokens.pop()
                User.old_url_tokens.add(token)
                url = User.URL_TEMPLATE.format(token) + User.QUERY_PARAMS.format('0')
            else:
                return None
        except Exception as e:
            raise Exception('get_new_url warning：%s %s ' % (e.args, url))
        # print(url)
        flag = not flag
        return url

    # 保存数据库
    def save(self, data):
        cur = User.con.cursor()
        if len(data['badge']) > 0:
            data['badge'] = json.dumps(data['badge'])

        sql = "replace into user values ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}'," \
              " '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}','{}', '{}', '{}', '{}', '{}')".format(
            data['id'], data['url_token'], data['answer_count'], data['asks'], data['articles_count'],
            data['columns'], data['pins'], data['incAnswers'], data['incPosts'], data['agrees'],
            data['thanks'], data['collections'], data['renke'], data['logs'], data['badge'],
            data['follower_count'], data['gender'], data['headline'], data['is_advertiser'], data['is_org'],
            data['name'], data['type'], data['url'], data['user_type'], datetime.datetime.now())
        # print(sql)
        cur.execute(sql)
        User.con.commit()
        cur.close()

    # 关闭数据库连接
    def close(self):
        User.con.close()
