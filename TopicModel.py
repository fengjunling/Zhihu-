import datetime
import threading
import time

from bs4 import BeautifulSoup

import db
import Main
from ZhihuLogin import ZhihuAccount
import json

'''
******已完成*****
info:话题爬取与解析

'''


class Topic(object):
    # 数据库连接
    con = db.DbUtil.connect()
    # 话题队列
    urls = []
    topic_tokens = set()
    # 错误信息 捕获后等待重新请求
    error_tokens = set()
    # 根话题
    URL_TEMPLATE = "https://www.zhihu.com/topic/19776749/organize/entire"
    QUERY_PARAMS = "?child={0}&parent={1}"

    def __init__(self, account, domin):
        self.session = account.session
        self.domin = domin

    def get_new_url(self):
        url = Topic.urls.pop(0)
        if isinstance(url, list):
            url = Topic.URL_TEMPLATE + Topic.QUERY_PARAMS.format(url[0], url[1])
        # print(url)
        return url

    def get_token_url(self, token):
        url = 'https://www.zhihu.com/topic/{0}/hot'
        return url.format(token)

    # 解析話題列表
    def parse_topic(self, data, parent=None):

        if parent is None:
            parent = data[0][2]
            # 去除已请求过的父元素
            data.pop(0)

        try:
            for x in data:
                if len(x) > 0:
                    if isinstance(x[0], list):
                        self.parse_topic(x, parent)
                    else:
                        if x[0] == 'topic':
                            resp = self.request_infos(self.get_token_url(x[2]))
                            # 参数x测试用
                            data = self.parse_infos(resp.text, x)
                            data['token'] = x[2]
                            data['parent'] = parent
                            try:
                                Main.user_lock.acquire()
                                print('%s 正在保存话题 %s' % (threading.current_thread().name, x[1]))
                                self.save(data)
                                Main.user_lock.release()
                            except Exception as e:
                                Main.x_lock.acquire()
                                with open('./logs/'+time.strftime("%Y-%m-%d", time.localtime())+'.txt', 'a', encoding='utf-8') as f:
                                    f.write(threading.current_thread().name + str(e.args) + str(
                                        datetime.datetime.now()) + '\r\n')
                                Main.user_lock.release()
                                Main.x_lock.release()
                                # print('topic save failed: %s' % (e.args,))
                        else:
                            Topic.urls.append([x[2], x[3]])
                else:
                    pass
        except Exception as e:
            Main.x_lock.acquire()
            with open('./logs/'+time.strftime("%Y-%m-%d", time.localtime())+'.txt', 'a', encoding='utf-8') as f:
                f.write(threading.current_thread().name + str(e.args) + str(datetime.datetime.now()) + '\r\n')
            Main.x_lock.release()
            # print('topic parse failed: %s' % (e.args,))

    # 话题详情页
    def request_infos(self, token=None):
        response = self.session.get(token)
        self.session.cookies.save()
        if response.status_code == 200:
            return response
        raise Exception('线程 %s 下载话题详情：%s 失败 响应状态码 %s' % (threading.current_thread().name, token, response.status_code))

    def parse_infos(self, text, token):
        soup = BeautifulSoup(text, 'lxml')
        # 获取desc,url,name,image,bestAnsweredCount,unansweredCount,questions
        res1 = soup.select('main.App-main meta')[0:7]
        # infos按序 followers,description,url,name,image,bestAnsweredCount,unansweredCount,zhihu:questionsCount
        infos = {}
        try:
            # 获取followers
            res2 = soup.select('div.ContentLayout-sideColumn div.Card button strong')
            infos['followers'] = res2[0].attrs['title']
        except Exception as e:
            with open('./logs/'+time.strftime("%Y-%m-%d", time.localtime())+'.txt', 'a', encoding='utf-8') as f:
                f.write(threading.current_thread().name + str(e.args) + str(datetime.datetime.now()) + '\r\n')
            # print('topic_info parse failed: %s' % (e.args,))

        for n in res1:
            infos[n.attrs['itemprop']] = n.attrs['content']
            # print(n.attrs['itemprop'] + " " + n.attrs['content'])
        return infos

    # 請求話題數據
    def request_topic(self, url=None):
        # 更新token
        Main.session_lock.acquire()
        self.session.headers.update({
            'x-xsrftoken': self._update_xsrf()
        })
        _xsrf = self.session.headers['x-xsrftoken']
        Main.session_lock.release()
        response = self.session.post(url, data={'_xsrf': _xsrf})
        self.session.cookies.save()
        if response.status_code == 200:
            return response
        raise Exception('线程 %s 请求话题：%s 失败 响应状态码 %s' % (threading.current_thread().name, url, response.status_code))

    def _update_xsrf(self):
        '''
        更新header的请求头
        :return:
        '''
        # self.session.cookies.load(ignore_discard=True)
        for c in self.session.cookies:
            if c.name == '_xsrf':
                return c.value

    # 保存数据库
    def save(self, data):
        cur = Topic.con.cursor()
        sql = "replace into topic values (default ,'{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(
            data['token'],
            data['name'],
            data['url'],
            json.dumps(data['description']),
            data['parent'],
            data[
                'followers'],
            data[
                'zhihu:bestAnswersCount'],
            data[
                'zhihu:unansweredCount'],
            data[
                'zhihu:questionsCount'],
            datetime.datetime.now())
        # print(sql)
        cur.execute(sql)
        Topic.con.commit()
        cur.close()

    # 关闭数据库连接
    def close(self):
        Topic.con.close()
