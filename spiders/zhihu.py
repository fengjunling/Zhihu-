import json

data = json.loads('{"msg": [["topic", "\u300c\u6839\u8bdd\u9898\u300d", "19776749"], [[["topic", "\u300c\u672a\u5f52\u7c7b\u300d\u8bdd\u9898", "19776751"], [[["load", "\u663e\u793a\u5b50\u8bdd\u9898", "", "19776751"], []]]], [["topic", "\u5b66\u79d1", "19618774"], [[["load", "\u663e\u793a\u5b50\u8bdd\u9898", "", "19618774"], []]]], [["topic", "\u5b9e\u4f53", "19778287"], [[["load", "\u663e\u793a\u5b50\u8bdd\u9898", "", "19778287"], []]]], [["topic", "\u300c\u5f62\u800c\u4e0a\u300d\u8bdd\u9898", "19778298"], [[["load", "\u663e\u793a\u5b50\u8bdd\u9898", "", "19778298"], []]]], [["topic", "\u4ea7\u4e1a", "19560891"], [[["load", "\u663e\u793a\u5b50\u8bdd\u9898", "", "19560891"], []]]], [["topic", "\u751f\u6d3b\u3001\u827a\u672f\u3001\u6587\u5316\u4e0e\u6d3b\u52a8", "19778317"], [[["load", "\u663e\u793a\u5b50\u8bdd\u9898", "", "19778317"], []]]]]], "r": 0}')
print(data)
for x in data['msg']: