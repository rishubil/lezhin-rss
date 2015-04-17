# -*- coding: utf-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
import os


class Config(object):
    SECRET_KEY = "lezhin-rss-secret-@nf%sf3g$sJ6jn"
    SQLALCHEMY_DATABASE_URI = "sqlite:///db/lezhin.db"
    debug = False


class Production(Config):
    debug = False
    CSRF_ENABLED = True


class Debug(Config):
    debug = True
    CSRF_ENABLED = False
