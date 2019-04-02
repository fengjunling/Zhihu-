import json
from multiprocessing import Lock
from multiprocessing.dummy import Pool
from time import clock

from spiders.Topic import Topic
from spiders.ZhihuLogin import ZhihuAccount


def partial_send_request(send_request, lock):
    pass

'''

info:程序入口

'''
if __name__ == '__main__':
    account = ZhihuAccount('15937829283', 'zhihumima1234')
    is_login = account.login(captcha_lang='en', load_cookies=True)
    topic = Topic(account, ZhihuAccount.con)

    urls = []
    begin = True

    # pool = Pool(8)
    # lock = Lock()
    # partial_send_request(send_request, lock=lock)
    # pool.map(partial_send_request)
    # pool.close()
    # pool.join()
    if is_login:
        start_time = clock()
        while len(urls) > 0 or begin == True:
            # 若为第一次请求
            if begin:
                resp = topic.request_topic()
                parent = '19776749'
                begin = False
            else:
                resp = topic.request_topic(urls[0])
                parent = urls[0][1]
                # 去除已请求过的连接
                urls.pop(0)
            data = json.loads(resp.text)
            data_list = topic.parse_topic(data['msg'], data_list=[])
            # 剔除第一个(数据重复)
            data_list.pop(0)

            for x in data_list:
                try:
                    if len(x) > 0:
                        if x[0] == 'topic':
                            infos = topic.parse_infos(topic.request_infos(x[2]))
                            topic.save([x[2], x[1], parent, infos])
                            print(x)
                        elif x[0] == 'load':
                            urls.append([x[2], x[3]])
                    else:
                        pass
                except Exception as e:
                    with open('./log.txt', 'a') as f:
                        f.write(str(e.args) + '\r\n')
                    print(e.args)

            print("请求中...")

        end_time = clock() - start_time
    else:
        print("爬取失败")
    # 关闭数据库连接
    ZhihuAccount.con.close()

    print(urls)
