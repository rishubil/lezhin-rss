# -*- coding: utf-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
from app import db
import json
from datetime import datetime


class Comic(db.Model):
    __tablename__ = 'comics'

    uid = db.Column(db.Integer)
    original_json = db.Column(db.Text)
    adult = db.Column(db.Boolean)
    artist_display_name = db.Column(db.String(100))
    comic_id = db.Column(db.String(100), primary_key=True)
    comment = db.Column(db.Text)
    genre = db.Column(db.String(50))
    published = db.Column(db.DateTime)
    schedule = db.Column(db.String(50))
    synopsis = db.Column(db.Text)
    title = db.Column(db.String(120))
    updated = db.Column(db.DateTime)

    last_updated = db.Column(db.DateTime)

    # episodes (backref)

    def __init__(self, json_string):
        self.original_json = json_string
        temp = json.loads(json_string)
        self.uid = temp.get('id')
        self.adult = temp.get('isAdult')
        artists = temp.get('artists')
        if artists:
            self.artist_display_name = "/".join(artist.get('name') for artist in artists)

        display = temp.get('display')
        if display:
            self.synopsis = display.get('synopsis')
            self.title = display.get('title')
            self.comment = display.get('comment')
            self.schedule = display.get('schedule')

        self.comic_id = temp.get('alias')
        genres = temp.get('genres')
        if genres and all(genre for genre in genres):
            self.genre = ", ".join(genres)
        publishedAt = temp.get('publishedAt')
        if publishedAt:
            self.published = datetime.fromtimestamp(publishedAt / 1000)
        updatedAt = temp.get('updatedAt')
        if updatedAt:
            self.updated = datetime.fromtimestamp(updatedAt / 1000)
        self.last_updated = datetime.now()


class Episode(db.Model):
    __tablename__ = 'episodes'

    uid = db.Column(db.Integer)
    seq = db.Column(db.Integer)
    original_json = db.Column(db.Text)
    artist_comment = db.Column(db.String(200))
    banner = db.Column(db.String(300))
    comic_id = db.Column(db.String(50), db.ForeignKey('comics.comic_id'))
    display_name = db.Column(db.String(100))
    episode_id = db.Column(db.String(100), primary_key=True)
    free = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(10))
    published = db.Column(db.DateTime)
    title = db.Column(db.String(120))
    updated = db.Column(db.DateTime)

    last_updated = db.Column(db.DateTime)

    comic = db.relationship('Comic',
                            backref=db.backref('episodes', lazy='dynamic', order_by=(db.desc(published), db.desc(seq))))

    def __init__(self, json_string):
        self.original_json = json_string
        temp = json.loads(json_string)
        self.uid = temp.get('id')
        self.seq = temp.get('seq')

        display = temp.get('display')
        if display:
            self.artist_comment = display.get('artistComment')
            self.display_name = display.get('displayName')
            self.title = display.get('title')

        # self.banner = temp.get('thumb')  # it must be added manually
        self.episode_id = temp.get('id')
        self.free = temp.get('badge') == 'f'
        self.name = temp.get('name')
        publishedAt = temp.get('publishedAt')
        if publishedAt:
            self.published = datetime.fromtimestamp(publishedAt / 1000)
        updatedAt = temp.get('updatedAt')
        if updatedAt:
            self.updated = datetime.fromtimestamp(updatedAt / 1000)
        self.last_updated = datetime.now()
