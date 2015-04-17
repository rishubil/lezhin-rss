# -*- coding: utf-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

from app.models import Comic, Episode
from app import db

if __name__ == "__main__":
    try:
        result = dict()
        comics = Comic.query.all()
        result['comics_json'] = [comic.original_json for comic in comics]
        episodes = Episode.query.all()
        result['episodes_json'] = [episode.original_json for episode in episodes]

        Comic.query.delete()
        Episode.query.delete()

        for comic_json in result['comics_json']:
            db.session.add(Comic(comic_json))

        for episode_json in result['episodes_json']:
            db.session.add(Episode(episode_json))
        db.session.commit()
    except:
        db.session.rollback()