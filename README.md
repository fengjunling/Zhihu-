# 知乎爬虫系统进度
系统分为知乎登陆，话题爬取，用户爬取三部分<br>
前两部分已完成 ，用户爬取未实现<br>
数据库包括：<br>
Topic(id,token,name,url,desc,parent,followers...10)<br>
User(id,answer_count,name,articles_count,gender,followers...17)<br>
spiders文件夹内文件说明：<br>
main.py:程序入口文件<br>
zhihulogin.py:登陆模块<br>
Topic.py:话题爬取与解析<br>
User.py:用户爬取与解析（未完成）<br>
encrypt.js:知乎登陆数据加密文件<br>
cookies:cookie存储文件<br>
captcha.jpg:登陆验证码<br>
db.py:数据库连接文件<br>
log.txt:错误日志文件<br>
requirements.txt:系统必备库列表<br>