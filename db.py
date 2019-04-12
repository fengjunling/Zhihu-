# coding: utf-8

import mysql.connector


class DbUtil:
    __host = 'localhost'
    __database = 'zhihutest'
    __user = 'root'
    __password = ''

    @classmethod
    def set_host(cls, host):
        cls.__host = host

    @classmethod
    def set_db(cls, db):

        cls.__db = db

    @classmethod
    def set_user(cls, user):
        cls.__user = user

    @classmethod
    def set_password(cls, password):
        cls.__password = password

    def __init__(self):
        pass

    @classmethod
    def connect(cls):
        cnx = mysql.connector.connect(host=cls.__host,
                                      database=cls.__database,
                                      user=cls.__user,
                                      password=cls.__password)
        return cnx

    @classmethod
    def close(cls, cursor, cnx):
        if cursor:
            cursor.close()
        if cnx:
            cnx.close()
