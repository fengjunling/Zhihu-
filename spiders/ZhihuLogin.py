# -*- coding: utf-8 -*-
import getpass
import threading

from spiders import db
from spiders import TopicModel

"""
info:
author:CriseLYJ
github:https://github.com/CriseLYJ/
update_time:2019-3-6
"""
import base64
import hashlib
import hmac
import json
import re
import time
from http import cookiejar
from urllib.parse import urlencode
from bs4 import BeautifulSoup

import execjs
import requests
from PIL import Image


class ZhihuAccount(object):

    def __init__(self, username: str = None, password: str = None):
        self.username = username
        self.password = password

        self.login_data = {
            'client_id': 'c3cef7c66a1843f8b3a9e6a1e3160e20',
            'grant_type': 'password',
            'source': 'com.zhihu.web',
            'username': '',
            'password': '',
            'lang': 'en',
            'ref_source': 'homepage',
            'utm_source': ''
        }
        # self.login_data = {
        #     'clientId': "c3cef7c66a1843f8b3a9e6a1e3160e20",
        #     'grantType': "password",
        #     'timestamp': 1553735401832,
        #     'source': "com.zhihu.web",
        #     'signature': "6524f270f3e01f52d57155a2522ec301b80e1c30",
        #     'username': "+8615937829283",
        #     'password': "zhihumima123",
        #     'captcha': "",
        #     'lang': "cn",
        #     'refSource': "homepage",
        #     'utmSource': ""
        # }

        self.session = requests.session()
        self.session.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'zh-CN,zh;q=0.9',
            'accept-encoding': 'gzip, deflate',
            'Host': 'www.zhihu.com',
            'Referer': 'https://www.zhihu.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'
        }
        self.session.cookies = cookiejar.LWPCookieJar(filename='./cookies.txt')

    def login(self, captcha_lang: str = 'en', load_cookies: bool = True):
        """
        模拟登录知乎
        :param captcha_lang: 验证码类型 'en' or 'cn'
        :param load_cookies: 是否读取上次保存的 Cookies
        :return: bool
        若在 PyCharm 下使用中文验证出现无法点击的问题，
        需要在 Settings / Tools / Python Scientific / Show Plots in Toolwindow，取消勾选
        """
        if load_cookies and self.load_cookies():
            print('读取 Cookies 文件')
            if self.check_login():
                print('登录成功')
                return True
            print('Cookies 已过期')

        self._check_user_pass()
        self.login_data.update({
            'username': self.username,
            'password': self.password,
            'lang': captcha_lang
        })

        headers = self.session.headers.copy()
        headers.update({
            'content-type': 'application/x-www-form-urlencoded',
            'x-zse-83': '3_1.1',
            'x-xsrftoken': self._get_xsrf()
        })

        # timestamp = int(time.time() * 1000)
        timestamp = int(round(time.time() * 1000))
        self.login_data.update({
            'captcha': self._get_captcha(headers=headers),
            'timestamp': timestamp,
            'signature': self._get_signature(timestamp)
        })
        data = self._encrypt(self.login_data)
        login_api = 'https://www.zhihu.com/api/v3/oauth/sign_in'

        resp = self.session.post(login_api, data=data, headers=headers)

        if 'error' in resp.text:
            print(json.loads(resp.text)['error'])
        if self.check_login():
            print('登录成功')
            return True
        print('登录失败')
        return False

    def load_cookies(self):
        """
        读取 Cookies 文件加载到 Session
        :return: bool
        """
        try:
            self.session.cookies.load(ignore_discard=True)
            return True
        except FileNotFoundError:
            return False

    def check_login(self):
        """
        检查登录状态，访问登录页面出现跳转则是已登录，
        如登录成功保存当前 Cookies
        :return: bool
        """
        login_url = 'https://www.zhihu.com/signup'
        resp = self.session.get(login_url, allow_redirects=False)
        if resp.status_code == 302:
            self.session.cookies.save()
            return True
        return False

    def _update_xsrf(self):
        '''
        更新header的请求头
        :return:
        '''
        self.session.cookies.load(ignore_discard=True)
        for c in self.session.cookies:
            if c.name == '_xsrf':
                return c.value

    def _get_xsrf(self):
        """
        从登录页面获取 xsrf
        :return: str
        """
        self.session.get('https://www.zhihu.com/', allow_redirects=False)
        for c in self.session.cookies:
            if c.name == '_xsrf':
                return c.value
        raise AssertionError('获取 xsrf 失败')

    def _get_captcha(self, lang: str = 'en'):
        """
        请求验证码的 API 接口，无论是否需要验证码都需要请求一次
        如果需要验证码会返回图片的 base64 编码
        根据 lang 参数匹配验证码，需要人工输入
        :param lang: 返回验证码的语言(en/cn)
        :return: 验证码的 POST 参数
        """

        headers = {
            "authorization": "oauth c3cef7c66a1843f8b3a9e6a1e3160e20",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'
        }

        if lang == 'cn':
            api = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=cn'
        else:
            api = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=en'
        resp = self.session.get(api, headers=headers)
        print('resp')
        print(resp.text)
        show_captcha = re.search(r'true', resp.text)

        if show_captcha:
            put_resp = self.session.put(api, headers=headers)
            json_data = json.loads(put_resp.text)
            img_base64 = json_data['img_base64'].replace(r'\n', '')
            with open('./captcha.jpg', 'wb') as f:
                f.write(base64.b64decode(img_base64))
            img = Image.open('./captcha.jpg')
            if lang == 'cn':
                import matplotlib.pyplot as plt
                plt.imshow(img)
                print('点击所有倒立的汉字，在命令行中按回车提交')
                points = plt.ginput(7)
                capt = json.dumps({'img_size': [200, 44],
                                   'input_points': [[i[0] / 2, i[1] / 2] for i in points]})
            else:
                img_thread = threading.Thread(target=img.show, daemon=True)
                img_thread.start()
                capt = input('请输入图片里的验证码：')
            # 这里必须先把参数 POST 验证码接口
            self.session.post(api, data={'input_text': capt})
            return capt
        return ''

    def _get_signature(self, timestamp: int or str):
        """
        通过 Hmac 算法计算返回签名
        实际是几个固定字符串加时间戳
        :param timestamp: 时间戳
        :return: 签名
        """
        ha = hmac.new(key='d1b964811afb40118a12068ff74a12f4'.encode('utf-8'), digestmod=hashlib.sha1)
        # ha = hmac.new(b'd1b964811afb40118a12068ff74a12f4', digestmod=hashlib.sha1)
        grant_type = self.login_data['grant_type']
        client_id = self.login_data['client_id']
        source = self.login_data['source']
        ha.update(bytes((grant_type + client_id + source + str(timestamp)), 'utf-8'))
        return ha.hexdigest()

    def _check_user_pass(self):
        """
        检查用户名和密码是否已输入，若无则手动输入
        """
        if not self.username:
            self.username = input('请输入手机号：')
        if self.username.isdigit() and '+86' not in self.username:
            self.username = '+86' + self.username

        if not self.password:
            # 输入密码不可见
            self.password = input("password:")

    @staticmethod
    def _encrypt(form_data: dict):
        with open('./encrypt.js', 'r') as f:
            js = execjs.compile(f.read())
            print(urlencode(form_data))
            return js.call('Q', urlencode(form_data))


# 解析話題列表
def parseTopic(data, data_list=[]):
    for x in data:
        if len(x) > 0 and isinstance(x[0], list):
            parseTopic(x, data_list)
        else:
            data_list.append(x)
    return data_list


# 话题详情页
def requestTopicInfos(token=None):
    # 更新token
    account.session.headers.update({
        'x-xsrftoken': account._update_xsrf()
    })

    if token is not None:
        response = account.session.get(
            domin + "/topic/" + token + "/hot", headers=account.session.headers, cookies=account.session.cookies)
    account.session.cookies.save()
    return response.text


def parseTopicInfos(text):
    soup = BeautifulSoup(text, 'lxml')
    # 获取desc,url,name,image,bestAnsweredCount,unansweredCount,questions
    res1 = soup.select('main.App-main meta')[0:7]
    # 获取followers
    res2 = soup.select('div.ContentLayout-sideColumn div.Card button strong')
    # infos按序 followers,desc,url,name,image,bestAnsweredCount,unansweredCount,questions
    infos = {}
    infos['followers'] = res2[0].attrs['title']
    for n in res1:
        infos[n.attrs['itemprop']] = n.attrs['content']
        # print(n.attrs['itemprop'] + " " + n.attrs['content'])
    return infos


# 請求話題數據
def requestTopic(datas=None):
    # 更新token
    account.session.headers.update({
        'x-xsrftoken': account._update_xsrf()
    })
    _xsrf = account.session.headers['x-xsrftoken']

    if datas is None:
        response = account.session.post(domin + "/topic/19776749/organize/entire", data={'_xsrf': _xsrf},
                                        headers=account.session.headers, cookies=account.session.cookies)
    else:
        response = account.session.post(
            domin + "/topic/19776749/organize/entire?child=" + datas[0] + "&parent=" + datas[1], data={'_xsrf': _xsrf},
            headers=account.session.headers, cookies=account.session.cookies)
    account.session.cookies.save()
    return response


# 保存数据库
def save(data):
    cur = con.cursor()
    sql = "insert into topic values (default ,'{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(data[0], data[1],
                                                                                                    data[3]['url'],
                                                                                                    data[3][
                                                                                                        'description'],
                                                                                                    data[2],
                                                                                                    data[3][
                                                                                                        'followers'],
                                                                                                    data[3][
                                                                                                        'zhihu:bestAnswersCount'],
                                                                                                    data[3][
                                                                                                        'zhihu:unansweredCount'],
                                                                                                    data[3][
                                                                                                        'zhihu:questionsCount'])
    cur.execute(sql)
    con.commit()
    cur.close()


if __name__ == '__main__':
    account = ZhihuAccount('15937829283', 'zhihumima1234')
    is_login = account.login(captcha_lang='en', load_cookies=True)
    domin = 'https://www.zhihu.com'

    # 连接数据库
    con = db.DbUtil.connect()
    urls = []
    begin = True
    # 统计请求条数
    count = 0
    if is_login:
        while len(urls) > 0 or begin == True:
            # 若为第一次请求
            if begin:
                resp = requestTopic()
                parent = '19776749'
                begin = False
            else:
                resp = requestTopic(urls[0])
                parent = urls[0][1]
                # 去除已请求过的连接
                urls.pop(0)
            data = json.loads(resp.text)
            data_list = parseTopic(data['msg'], data_list=[])
            # 剔除第一个(数据重复)
            data_list.pop(0)

            for x in data_list:
                try:
                    if len(x) > 0:
                        if x[0] == 'topic':
                            infos = parseTopicInfos(requestTopicInfos(x[2]))
                            save([x[2], x[1], parent, infos])
                            print(x)
                        elif x[0] == 'load':
                            urls.append([x[2], x[3]])
                    else:
                        pass
                except Exception as e:
                    with open('./log.txt', 'a') as f:
                        f.write(str(e.args)+'\r\n')
                    print(e.args)

            print("请求中...")
    else:
        print("爬取失败")
    # 关闭数据库连接
    con.close()
    print(urls)
