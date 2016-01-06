# -*- coding: utf-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
from app import db
import json
from datetime import datetime


def timestamp_to_datetime(timestamp):
    return datetime.fromtimestamp(timestamp / 1000)


def dump(inst, cls):
    convert = dict()
    d = dict()
    for c in cls.__table__.columns:
        v = getattr(inst, c.name)
        if c.type in convert.keys() and v is not None:
            try:
                d[c.name] = convert[c.type](v)
            except:
                d[c.name] = "Error:  Failed to covert using ", str(convert[c.type])
        elif v is None:
            d[c.name] = str()
        else:
            d[c.name] = v
    return d


class Comic(db.Model):
    __tablename__ = 'comics'
    DATETIME_COLUMNS = ('created', 'updated', 'published')

    comicId = db.Column(db.String(255), primary_key=True)
    title = db.Column(db.String(255))
    htmlTitle = db.Column(db.String(255))
    description = db.Column(db.String(255))
    artists = db.Column(db.String(255))
    artistDisplayName = db.Column(db.String(255))
    created = db.Column(db.DateTime)
    updated = db.Column(db.DateTime)
    adult = db.Column(db.Boolean)
    completed = db.Column(db.Integer)
    hasSide = db.Column(db.Boolean)
    printed = db.Column(db.Boolean)
    days = db.Column(db.String(255))
    schedule = db.Column(db.String(255))
    blind = db.Column(db.String(255))
    # ignore color
    newly = db.Column(db.Boolean)
    genre = db.Column(db.String(255))
    synopsis = db.Column(db.Text)
    comment = db.Column(db.Text)
    todayComment = db.Column(db.Text)
    editorComment = db.Column(db.Text)
    notice = db.Column(db.String(255))
    covers = db.Column(db.Integer)
    banners = db.Column(db.Integer)
    relatedComics = db.Column(db.Text)
    crossView = db.Column(db.Boolean)
    bgm = db.Column(db.Boolean)
    # ignore authors
    localRating = db.Column(db.String(255))
    published = db.Column(db.DateTime)
    up = db.Column(db.Integer)
    seq = db.Column(db.Integer)

    def __init__(self, comic_dict):
        for name, value in comic_dict.iteritems():
            if hasattr(self, name):
                if name in Comic.DATETIME_COLUMNS:
                    value = timestamp_to_datetime(value)
                setattr(self, name, value)

    @property
    def dump(self):
        return dump(self, self.__class__)


class Episode(db.Model):
    __tablename__ = 'episodes'
    DATETIME_COLUMNS = ('published', 'freed')

    episodeId = db.Column(db.String(255), primary_key=True)
    seq = db.Column(db.Integer)
    comicId = db.Column(db.String(255), db.ForeignKey('comics.comicId'))
    name = db.Column(db.String(255))
    displayName = db.Column(db.String(255))
    title = db.Column(db.String(255))
    artists = db.Column(db.String(255))
    description = db.Column(db.String(255))
    cover = db.Column(db.String(255))
    banner = db.Column(db.String(255))
    social = db.Column(db.String(255))
    cut = db.Column(db.Integer)
    page = db.Column(db.Integer)
    type = db.Column(db.String(255))
    coin = db.Column(db.Integer)
    point = db.Column(db.Integer)
    free = db.Column(db.Boolean, default=False)
    freeDate = db.Column(db.String(255))
    up = db.Column(db.Boolean, default=False)
    dDay = db.Column(db.Integer)
    artistComment = db.Column(db.String(255))
    direction = db.Column(db.String(255))
    published = db.Column(db.DateTime)
    freed = db.Column(db.DateTime)

    def __init__(self, episode_dict):
        for name, value in episode_dict.iteritems():
            if hasattr(self, name):
                if name in Episode.DATETIME_COLUMNS:
                    value = timestamp_to_datetime(value)
                setattr(self, name, value)

    @property
    def dump(self):
        return dump(self, self.__class__)
