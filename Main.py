import datetime
import time
import json
import threading

import TopicModel
import UserModel
import db

from ZhihuLogin import ZhihuAccount

'''

info:程序入口

'''
# 读写日志锁
x_lock = threading.Lock()
# 数据库锁
topic_lock = threading.Lock()
user_lock = threading.Lock()
# session锁
session_lock = threading.Lock()


def request_topic():
    start_time = time.time()
    TopicModel.Topic.urls.append(TopicModel.Topic.URL_TEMPLATE)
    # 多线程
    topic_list = []

    for i in range(10):
        t = threading.Thread(target=start_request_topic, name=('Thread-Topic %s' % (str(i))))
        t.start()
        topic_list.append(t)

    for j in topic_list:
        j.join()

    end_time = time.time() - start_time
    print('爬取话题耗时: ' + str(end_time))


def start_request_topic():
    while len(TopicModel.Topic.urls) > 0:
        try:
            url = topic.get_new_url()
            resp = topic.request_topic(url)
            data = json.loads(resp.text)['msg']
            topic.parse_topic(data)
            print("线程 %s 请求进度...%s \n" % (threading.current_thread().name, len(TopicModel.Topic.urls)))
        except Exception as e:
            x_lock.acquire()
            with open('./logs/'+time.strftime("%Y-%m-%d", time.localtime())+'.txt', 'a', encoding='utf-8') as f:
                f.write(threading.current_thread().name + str(e.args) + str(datetime.datetime.now()) + '\r\n')
            x_lock.release()


def request_user():
    start_time = time.time()
    UserModel.User.new_url_tokens.add('kaifulee')
    # 多线程
    user_list = []

    for i in range(10):
        t = threading.Thread(target=start_request_user, name=('Thread-User %s' % (str(i))))
        t.start()
        user_list.append(t)

    for j in user_list:
        j.join()
    # start_request_user()

    end_time = time.time() - start_time
    print('爬取用户耗时' + str(end_time))


def start_request_user():
    while UserModel.User.new_url_tokens.__len__() > 0 or UserModel.User.next_urls.__len__() > 0:
        try:
            url = user.get_new_url()
            if url is not None:
                response = user.download(url)
                user.parse(response)
            print('线程 %s 正在请求... %s' % (threading.current_thread().name))
        except Exception as e:
            x_lock.acquire()
            with open('./logs/'+time.strftime("%Y-%m-%d", time.localtime())+'.txt', 'a', encoding='utf-8') as f:
                f.write(threading.current_thread().name + str(e.args) + str(datetime.datetime.now()) + '\r\n')
            x_lock.release()


if __name__ == '__main__':
    domin = "https://www.zhihu.com"

    # 得到一个知乎的连接
    account = ZhihuAccount('15937829283', 'zhihumima1234')
    is_login = account.login(captcha_lang='en', load_cookies=True)

    topic = TopicModel.Topic(account, domin)
    user = UserModel.User(account, domin)

    if is_login:

        # resp = user.get_user_home('guo-jia-32')
        # user.parse_home(resp)
        t1 = threading.Thread(target=request_topic, name='Thread-Topic')
        t2 = threading.Thread(target=request_user, name='Thread-User')

        t1.start()
        t2.start()

        t1.join()
        t2.join()

    else:
        print("爬取失败")

    # 关闭数据库连接
    topic.close()
    user.close()

    print("爬取结束")
