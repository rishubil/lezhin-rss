# -*- coding: utf-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
from app import db
import json
from datetime import datetime


class Comic(db.Model):
    __tablename__ = 'comics'

    original_json = db.Column(db.Text)
    adult = db.Column(db.Boolean)
    artist_display_name = db.Column(db.String(100))
    comic_id = db.Column(db.String(100), primary_key=True)
    comment = db.Column(db.Text)
    created = db.Column(db.DateTime)
    genre = db.Column(db.String(50))
    published = db.Column(db.DateTime)
    schedule = db.Column(db.String(50))
    seq = db.Column(db.Integer)
    synopsis = db.Column(db.Text)
    title = db.Column(db.String(120))
    updated = db.Column(db.DateTime)

    last_updated = db.Column(db.DateTime)

    # episodes (backref)

    def __init__(self, json_string):
        self.original_json = json_string;
        temp = json.loads(json_string)
        self.adult = temp['adult']
        self.artist_display_name = temp['artistDisplayName']
        self.comic_id = temp['comicId']
        self.comment = temp['comment']
        self.created = datetime.fromtimestamp(temp['created'] / 1000)
        self.genre = temp['genre']
        self.published = datetime.fromtimestamp(temp['published'] / 1000)
        self.schedule = temp['schedule']
        self.seq = temp['seq']
        self.synopsis = temp['synopsis']
        self.title = temp['title']
        self.updated = datetime.fromtimestamp(temp['updated'] / 1000)

        self.last_updated = datetime.now()


class Episode(db.Model):
    __tablename__ = 'episodes'

    original_json = db.Column(db.Text)
    artist_comment = db.Column(db.String(200))
    banner = db.Column(db.String(300))
    comic_id = db.Column(db.String(50), db.ForeignKey('comics.comic_id'))
    created = db.Column(db.DateTime)
    display_name = db.Column(db.String(100))
    episode_id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(10))
    published = db.Column(db.DateTime)
    seq = db.Column(db.Integer)
    title = db.Column(db.String(120))
    updated = db.Column(db.DateTime)

    last_updated = db.Column(db.DateTime)

    comic = db.relationship('Comic',
                            backref=db.backref('episodes', lazy='dynamic', order_by=(db.desc(published), db.desc(seq))))

    def __init__(self, json_string):
        self.original_json = json_string;
        temp = json.loads(json_string)
        self.artist_comment = temp['artistComment']
        self.banner = temp['banner']
        self.comic_id = temp['comicId']
        self.created = datetime.fromtimestamp(temp['created'] / 1000)
        self.display_name = temp['displayName']
        self.episode_id = temp['episodeId']
        self.name = temp['name']
        self.published = datetime.fromtimestamp(temp['published'] / 1000)
        self.seq = temp['seq']
        self.title = temp['title']
        self.updated = datetime.fromtimestamp(temp['updated'] / 1000)

        self.last_updated = datetime.now()
