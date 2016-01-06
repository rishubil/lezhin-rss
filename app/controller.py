# -*- coding: utf-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
from flask import render_template, request, redirect, url_for
from app import app, db
from app.models import Comic, Episode
import requests
import json
from datetime import datetime
from werkzeug.contrib.atom import AtomFeed, FeedEntry
from sqlalchemy import or_
from multiprocessing import Pool
import time

API_HEADER = {'Authorization': 'Bearer 5c5dcca6-b245-4eb4-bbd9-259b216977c7',
              'X-LZ-Version': '2.4.4',
              'X-Requested-With': 'X-Requested-With'}

API_URL_PREFIX = 'https://api.lezhin.com/v1/'
CDN_URL_PREFIX = 'http://cdn.lezhin.com/'

URL_HOME = 'http://www.lezhin.com/'
URL_GENRE = 'http://www.lezhin.com/#genre'
URL_COMIC_FORMAT = 'http://www.lezhin.com/comic/%s'
URL_EPISODE_FORMAT = 'http://www.lezhin.com/comic/%s'

API_URL_COMICS = API_URL_PREFIX + 'comics'
API_URL_EPISODES_FORMAT = API_URL_PREFIX + 'episodes/%s'
URL_COMIC_BANNER_FORMAT = CDN_URL_PREFIX + 'comics/%s/images/banners/%s'
URL_COMIC_THUMBNAIL_FORMAT = CDN_URL_PREFIX + 'comics/%s/images/thumbnail'
URL_COMIC_WIDE_FORMAT = CDN_URL_PREFIX + 'comics/%s/images/wide'
URL_EPISODE_BANNER_FORMAT = CDN_URL_PREFIX + 'episodes/%s/banners/1'

RSS_FEED_COUNT = 30
INDEX_ITEM_IN_ROW = 2
INDEX_PAGE_SIZE = 30
UPDATE_PROCESS_SIZE = 16
RETRY_MAX_COUNT = 5


def get_comics():
    print("[{0:s}] getting comics...".format(str(datetime.now()), ))
    r = None
    retry_count = RETRY_MAX_COUNT
    while retry_count > 0:
        try:
            r = requests.get(API_URL_COMICS, headers=API_HEADER)
            break
        except requests.exceptions.ConnectionError as e:
            print("[{0:s}] connection error. trying again...".format(str(datetime.now()), ))
            retry_count -= 1
            if retry_count <= 0:
                raise e
    result = json.loads(r.text)
    return [Comic(comic_dict) for comic_dict in result]


def get_episodes(comic_id):
    try:
        print("[{0:s}] getting episodes of {1:s}...".format(str(datetime.now()), comic_id))
        r = None
        retry_count = RETRY_MAX_COUNT
        while retry_count > 0:
            try:
                r = requests.get(API_URL_EPISODES_FORMAT % (comic_id,), headers=API_HEADER)
                break
            except requests.exceptions.ConnectionError as e:
                print("[{0:s}] connection error. trying again...".format(str(datetime.now()), ))
                retry_count -= 1
                if retry_count <= 0:
                    raise e
        result = json.loads(r.text)
        return [Episode(episode_dict) for episode_dict in result]
    except:
        import traceback

        print("[{0:s}] well, an error is coming.".format(str(datetime.now()), ))
        print(traceback.format_exc())


def update_db():
    start = time.time()
    result = dict()
    try:
        comics = sorted(get_comics(), key=lambda x: x.comicId)

        pool = Pool(processes=UPDATE_PROCESS_SIZE)
        episodes_list = pool.map(get_episodes, [comic.comicId for comic in comics])

        # episodes = [get_episodes(comic.comicId) for comic in comics]

        print("[{0:s}] commiting comics and episodes...".format(str(datetime.now()), ))
        db.session.query(Comic).delete()
        db.session.query(Episode).delete()
        for comic in comics:
            if Comic.query.get(comic.comicId) is None:
                db.session.add(comic)
        for episodes in episodes_list:
            for episode in episodes:
                if Episode.query.get(episode.episodeId) is None:
                    db.session.add(episode)
        db.session.commit()
        end = time.time()
        print("[{0:s}] done in {1:s} sec.".format(str(datetime.now()), str(end - start)))
        result['status'] = 'done'
    except:
        import traceback

        print("[{0:s}] well, an error is coming.".format(str(datetime.now()), ))
        print(traceback.format_exc())
        db.session.rollback()
        result['status'] = 'failed'
        result['description'] = dict()
        result['description']['title'] = traceback.format_exc().splitlines()[-1]
        result['description']['contents'] = traceback.format_exc()
    return json.dumps(result)


def comic_to_atom_item(comic):
    banner = URL_COMIC_BANNER_FORMAT % (comic.comicId, comic.banners)
    des_message = '<img src="%s"></img><p>[%s]</p><h3>"%s"</h3><p>%s</p>' % \
                  (banner, comic.genre, comic.comment, comic.synopsis)
    return FeedEntry(
        title="%s - %s" % (comic.title, comic.artistDisplayName),
        title_type='text',
        summary=des_message,
        summary_type='html',
        url=URL_COMIC_FORMAT % (comic.comicId,),
        published=comic.published,
        updated=comic.updated if (comic.updated - datetime(1970, 1, 1)).total_seconds() > 0 else comic.published,
        author=comic.artistDisplayName
    )


def episode_to_atom_item(episode):
    banner = URL_EPISODE_BANNER_FORMAT % (episode.episodeId, )
    des_message = '<img src="%s"></img><p>%s</p>' % (banner, episode.artistComment)
    return FeedEntry(
        title=episode.title,
        title_type='text',
        summary=des_message,
        summary_type='html',
        url=URL_EPISODE_FORMAT % (episode.episodeId,),
        published=episode.published,
        updated=episode.published,
        author=Comic.query.get(episode.comicId).artistDisplayName
    )


@app.route('/lezhin-rss/new.xml')
@app.route('/lezhin-rss/new.atom')
def new_atom():
    icon_url = "http://i.imgur.com/LJ0ru93.png"
    comics = Comic.query.order_by(Comic.published.desc()).limit(RSS_FEED_COUNT).all()
    atom_items = [comic_to_atom_item(comic) for comic in comics]

    atom = AtomFeed(
        "레진코믹스 새로운 만화",
        updated=comics[0].published,
        subtitle="레진코믹스에 새롭게 추가된 만화의 정보입니다.",
        subtitle_type='text',
        icon=icon_url,
        logo=icon_url,
        feed_url=request.url,
        url=URL_GENRE,
        entries=atom_items
    )

    return atom.get_response()


@app.route('/lezhin-rss/comic/<string:comic_id>.xml')
@app.route('/lezhin-rss/comic/<string:comic_id>.atom')
def comic_atom(comic_id):
    comic = Comic.query.get(comic_id)
    if comic is None:
        return "... 그런 만화가 없는데요?", 404
    episodes = Episode.query.filter_by(comicId=comic_id).order_by(Episode.published.desc(), Episode.seq.desc()).limit(
        RSS_FEED_COUNT).all()

    atom_items = [episode_to_atom_item(episode) for episode in episodes]
    atom_title = "%s - %s" % (comic.title, comic.artistDisplayName)

    atom = AtomFeed(
        atom_title,
        updated=episodes[0].published,
        subtitle=comic.synopsis,
        subtitle_type='text',
        icon=URL_COMIC_THUMBNAIL_FORMAT % (comic.comicId,),
        logo=URL_COMIC_THUMBNAIL_FORMAT % (comic.comicId,),
        feed_url=request.url,
        url=URL_GENRE,
        entries=atom_items
    )

    return atom.get_response()


@app.route('/lezhin-rss/comic/free/<string:comic_id>.xml')
@app.route('/lezhin-rss/comic/free/<string:comic_id>.atom')
def comic_free_atom(comic_id):
    comic = Comic.query.get(comic_id)
    if comic is None:
        return "... 그런 만화가 없는데요?", 404
    episodes = Episode.query.filter_by(comicId=comic_id, free=True) \
        .order_by(Episode.published.desc(), Episode.seq.desc()).limit(RSS_FEED_COUNT).all()

    atom_items = [episode_to_atom_item(episode) for episode in episodes]
    atom_title = "%s - %s" % (comic.title, comic.artistDisplayName)

    atom = AtomFeed(
        atom_title,
        updated=episodes[0].published,
        subtitle=comic.synopsis,
        subtitle_type='text',
        icon=URL_COMIC_THUMBNAIL_FORMAT % (comic.comicId,),
        logo=URL_COMIC_THUMBNAIL_FORMAT % (comic.comicId,),
        feed_url=request.url,
        url=URL_GENRE,
        entries=atom_items
    )

    return atom.get_response()


@app.route('/lezhin-rss/')
def index():
    context = dict()
    context['last_update'] = Episode.query.order_by(Episode.published.desc()) \
        .first().published.strftime("%Y-%m-%d %H:%M:%S")
    context['comics'] = api_comics()

    return render_template('index.html', context=context)



@app.route('/lezhin-rss/api/comics')
def api_comics():
    return json.dumps({'comics': [x.dump for x in Comic.query.all()]}, default=lambda obj: (
        obj.isoformat()
        if isinstance(obj, datetime)
        else None
    ), sort_keys=True)


@app.route('/lezhin-rss/api/episodes/<string:comic_id>')
def api_episodes(comic_id):
    return requests.get(API_URL_EPISODES_FORMAT % (comic_id,), headers=API_HEADER).text
