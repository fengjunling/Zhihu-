from bs4 import BeautifulSoup
from spiders.ZhihuLogin import *

'''
******未完成*****
info:用户爬取与解析

'''
class User(object):
    domin = 'https://www.zhihu.com'
    con = ZhihuAccount.con

    def __init__(self, account, con):
        self.session = account.session
        self.con = con

    # 解析話題列表
    def parse_user(self, data, data_list=[]):
        for x in data:
            if len(x) > 0 and isinstance(x[0], list):
                self.parse_user(x, data_list)
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
    def request_user(self, datas=None):
        # 更新token
        self.session.headers.update({
            'x-xsrftoken': self._update_xsrf()
        })
        _xsrf = self.session.headers['x-xsrftoken']

        # https://www.zhihu.com/people/mo-yu-JGH/activities
        # 获取其粉丝和关注者 两个url队列 set集合去重（如何解决死循环？互关陷入死循环）
        # /api/v4/members/mu-zhi-93-37/followers?
        # include=data%5B*%5D.answer_count%2Carticles_count%2Cgender%2Cfollower_count%2Cis_followed%2Cis_following%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&offset=0&limit=20
        if datas is None:
            response = self.session.post(User.domin + "/topic/19776749/organize/entire", data={'_xsrf': _xsrf})
        else:
            response = self.session.post(
                User.domin + "/topic/19776749/organize/entire?child=" + datas[0] + "&parent=" + datas[1], data={'_xsrf': _xsrf})
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
