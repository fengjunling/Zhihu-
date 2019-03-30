class TopicModel(object):
    __name = ""
    __desc = ""
    __parent = ""
    __sub = ""
    __followers = ""
    __ques_count = ""
    __create_time = ""

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value

    @property
    def desc(self):
        return self.__desc

    @desc.setter
    def desc(self, value):
        self.__desc = value

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, value):
        self.__parent = value

    @property
    def sub(self):
        return self.__sub

    @sub.setter
    def sub(self, value):
        self.__sub = value

    @property
    def followers(self):
        return self.__followers

    @sub.setter
    def followers(self, value):
        self.__ques_count = value

    @property
    def ques_count(self):
        return self.__ques_count

    @ques_count.setter
    def ques_count(self, value):
        self.__ques_count = value

    @property
    def create_time(self):
        return self.__create_time

    @ques_count.setter
    def create_time(self, value):
        self.__create_time = value