# 知乎爬虫系统进度
系统分为知乎登陆，话题爬取，用户爬取三部分<br>
前两部分已完成 ，用户爬取未实现<br>
数据库包括：
Topic(id,token,name,url,desc,parent,followers...10)
User(id,answer_count,name,articles_count,gender,followers...17)
spiders文件夹内文件说明：
main.py:程序入口文件
zhihulogin.py:登陆模块
Topic.py:话题爬取与解析
User.py:用户爬取与解析（未完成）
encrypt.js:知乎登陆数据加密文件
cookies:cookie存储文件
captcha.jpg:登陆验证码
db.py:数据库连接文件
log.txt:错误日志文件
requirements.txt:系统必备库列表