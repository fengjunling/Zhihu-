from bs4 import BeautifulSoup
from spiders.ZhihuLogin import *
from spiders.ZhihuLogin import ZhihuAccount

'''
******已完成*****
info:话题爬取与解析

'''
class Topic(object):
    domin = 'https://www.zhihu.com'
    con = ZhihuAccount.con

    def __init__(self, account, con):
        self.session = account.session
        self.con = con

    # 解析話題列表
    def parse_topic(self, data, data_list=[]):
        for x in data:
            if len(x) > 0 and isinstance(x[0], list):
                self.parse_topic(x, data_list)
            else:
                data_list.append(x)
        return data_list

    # 话题详情页
    def request_infos(self, token=None):
        # 更新token
        # self.session.headers.update({
        #     'x-xsrftoken': self._update_xsrf()
        # })

        if token is not None:
            response = self.session.get(
                Topic.domin + "/topic/" + token + "/hot")
        self.session.cookies.save()
        return response.text

    def parse_infos(self, text):
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
    def request_topic(self, datas=None):
        # 更新token
        self.session.headers.update({
            'x-xsrftoken': self._update_xsrf()
        })
        _xsrf = self.session.headers['x-xsrftoken']

        if datas is None:
            response = self.session.post(Topic.domin + "/topic/19776749/organize/entire", data={'_xsrf': _xsrf})
        else:
            response = self.session.post(
                Topic.domin + "/topic/19776749/organize/entire?child=" + datas[0] + "&parent=" + datas[1],
                data={'_xsrf': _xsrf})
        self.session.cookies.save()
        return response

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
        sql = "insert into topic values (default ,'{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(data[0],
                                                                                                        data[1],
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
        Topic.con.commit()
        cur.close()
