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
import PyRSS2Gen
from xml.sax.saxutils import escape, unescape
from werkzeug.contrib.atom import AtomFeed, FeedEntry
from sqlalchemy import or_, desc
from multiprocessing import Pool
import time
import re

URL_HOME = 'http://www.lezhin.com/'
URL_GENRE = 'http://www.lezhin.com/#genre'
URL_COMIC_PREFIX = 'http://www.lezhin.com/comic/'
URL_COMIC_THUMBNAIL_PREFIX = 'http://cdn.lezhin.com/comics/'
URL_COMIC_THUMBNAIL_POSTFIX = '/thumbnail'
URL_COMIC_BANNER_PREFIX = 'http://cdn.lezhin.com/comics/'
URL_COMIC_BANNER_POSTFIX = '/banners/1'
REGEX_COMICS = r'comics: (\[{.*}\]),specials:'
REGEX_EPISODES = r'all      : (\[{.*}\]),purchased:'
RSS_FEED_COUNT = 30
INDEX_ITEM_IN_ROW = 2
INDEX_PAGE_SIZE = 30
UPDATE_PROCESS_SIZE = 8

# escape() and unescape() takes care of &, < and >.
html_escape_table = {
    '\n': "<br/>",
    '"': "&quot;",
    "'": "&apos;"
}
html_unescape_table = {v: k for k, v in html_escape_table.items()}


def html_escape(text):
    return escape(text, html_escape_table)


def html_unescape(text):
    return unescape(text, html_unescape_table)


def find_all(a_str, sub, start=0):
    while True:
        start = a_str.find(sub, start)
        if start == -1:
            return
        yield start
        start += len(sub)


def get_comics(html):
    m = re.search(REGEX_COMICS, html)
    return json.loads(m.group(1))


def get_episodes(html):
    m = re.search(REGEX_EPISODES, html)
    return json.loads(m.group(1))


def get_episode_from_url(comic_id):
    #print("[{0:s}] updating episodes of {1:s}...".format(str(datetime.now()), comic_id))
    r = None
    retry_count = 3
    while retry_count > 0:
        try:
            r = requests.get(URL_COMIC_PREFIX + comic_id)
            break
        except requests.exceptions.ConnectionError as e:
            print("[{0:s}] connection error. trying again...".format(str(datetime.now()), ))
            retry_count -= 1
            if retry_count <= 0:
                raise e

    return get_episodes(r.text)


def update_db():
    start = time.time()
    result = dict()
    try:
        print("[{0:s}] updating comics...".format(str(datetime.now()), ))
        r1 = None
        retry_count = 3
        while retry_count > 0:
            try:
                r1 = requests.get(URL_GENRE)
                break
            except requests.exceptions.ConnectionError as e:
                print("[{0:s}] connection error. trying again...".format(str(datetime.now()), ))
                retry_count -= 1
                if retry_count <= 0:
                    raise e

        comics_loaded = get_comics(r1.text)
        comics = list()
        episodes = list()
        episodes_ids = list()
        for i, comic_loaded in enumerate(comics_loaded):
            comic = Comic(json.dumps(comic_loaded))
            comics.append(comic)
            episodes_ids.append(comic.comic_id)

        pool = Pool(processes=UPDATE_PROCESS_SIZE)
        episodes_loadeds = pool.map(get_episode_from_url, episodes_ids)

        for episodes_loaded in episodes_loadeds:
            for episode_loaded in episodes_loaded:
                json_string = json.dumps(episode_loaded)
                episode = Episode(json_string)
                episodes.append(episode)

        print("[{0:s}] commiting comics and episodes...".format(str(datetime.now()), ))
        db.session.query(Comic).delete()
        db.session.query(Episode).delete()
        for comic in comics:
            db.session.add(comic)
        for episode in episodes:
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


def comic_to_rss_item(comic):
    banner = URL_COMIC_BANNER_PREFIX + comic.comic_id + URL_COMIC_BANNER_POSTFIX
    des_message = '<img src="%s"></img><p>[%s]</p><h3>"%s"</h3><p>%s</p>' % (banner, comic.genre, comic.comment, comic.synopsis)
    return PyRSS2Gen.RSSItem(
        title="%s - %s" % (comic.title, comic.artist_display_name),
        link=URL_COMIC_PREFIX + comic.comic_id,
        description=des_message,
        guid=PyRSS2Gen.Guid(URL_COMIC_PREFIX + comic.comic_id),
        pubDate=comic.published
    )


def comic_to_atom_item(comic):
    banner = URL_COMIC_BANNER_PREFIX + comic.comic_id + URL_COMIC_BANNER_POSTFIX
    des_message = '<img src="%s"></img><p>[%s]</p><h3>"%s"</h3><p>%s</p>' % (banner, comic.genre, comic.comment, comic.synopsis)
    return FeedEntry(
        title="%s - %s" % (comic.title, comic.artist_display_name),
        title_type='text',
        summary=des_message,
        summary_type='html',
        url=URL_COMIC_PREFIX + comic.comic_id,
        published=comic.published,
        updated=comic.updated if (comic.updated - datetime(1970, 1, 1)).total_seconds() > 0 else comic.published,
        author=comic.artist_display_name
    )


def episode_to_rss_item(episode):
    des_message = '<img src="%s"></img><p>%s</p>' % (episode.banner, episode.artist_comment)
    return PyRSS2Gen.RSSItem(
        title=episode.title,
        link=URL_COMIC_PREFIX + episode.episode_id,
        description=des_message,
        guid=PyRSS2Gen.Guid(URL_COMIC_PREFIX + episode.episode_id),
        pubDate=episode.published
    )


def episode_to_atom_item(episode):
    des_message = '<img src="%s"></img><p>%s</p>' % (episode.banner, episode.artist_comment)
    return FeedEntry(
        title=episode.title,
        title_type='text',
        summary=des_message,
        summary_type='html',
        url=URL_COMIC_PREFIX + episode.episode_id,
        published=episode.published,
        updated=episode.published,
        author=episode.comic.artist_display_name
    )


@app.route('/lezhin-rss/new.xml')
def new_rss():
    icon_url = "http://i.imgur.com/LJ0ru93.png"
    comics = Comic.query.order_by(Comic.published.desc(), Comic.seq.desc()).limit(RSS_FEED_COUNT)
    rss_items = [comic_to_rss_item(comic) for comic in comics]

    title = "레진코믹스 새로운 만화"
    image = PyRSS2Gen.Image(icon_url, title, URL_HOME)

    rss = PyRSS2Gen.RSS2(
        title=title,
        link=URL_GENRE,
        description="레진코믹스에 새롭게 추가된 만화의 정보입니다.",
        language='ko',
        lastBuildDate=comics[0].last_updated,
        image=image,
        items=rss_items)

    return rss.to_xml(encoding="utf-8")


@app.route('/lezhin-rss/new.atom')
def new_atom():
    icon_url = "http://i.imgur.com/LJ0ru93.png"
    comics = Comic.query.order_by(Comic.published.desc(), Comic.seq.desc()).limit(RSS_FEED_COUNT)
    atom_items = [comic_to_atom_item(comic) for comic in comics]

    atom = AtomFeed(
        "레진코믹스 새로운 만화",
        updated=comics[0].last_updated,
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
def comic_rss(comic_id):
    comic = Comic.query.get(comic_id)
    if comic is None:
        return "... 그런 만화가 없는데요?", 404
    episodes = comic.episodes[0:RSS_FEED_COUNT]

    rss_items = [episode_to_rss_item(episode) for episode in episodes]
    rss_title = "%s - %s" % (comic.title, comic.artist_display_name)
    image = PyRSS2Gen.Image(URL_COMIC_THUMBNAIL_PREFIX + comic_id +
                            URL_COMIC_THUMBNAIL_POSTFIX, rss_title, URL_COMIC_PREFIX + comic_id)
    rss = PyRSS2Gen.RSS2(
        title=rss_title,
        link=URL_COMIC_PREFIX + comic_id,
        description=comic.synopsis,
        language='ko',
        lastBuildDate=comic.last_updated,
        image=image,
        items=rss_items)

    return rss.to_xml(encoding="utf-8")


@app.route('/lezhin-rss/comic/<string:comic_id>.atom')
def comic_atom(comic_id):
    comic = Comic.query.get(comic_id)
    if comic is None:
        return "... 그런 만화가 없는데요?", 404
    episodes = comic.episodes[0:RSS_FEED_COUNT]

    atom_items = [episode_to_atom_item(episode) for episode in episodes]
    atom_title = "%s - %s" % (comic.title, comic.artist_display_name)

    atom = AtomFeed(
        atom_title,
        updated=comic.last_updated,
        subtitle=comic.synopsis,
        subtitle_type='text',
        icon=URL_COMIC_THUMBNAIL_PREFIX + comic_id + URL_COMIC_THUMBNAIL_POSTFIX,
        logo=URL_COMIC_THUMBNAIL_PREFIX + comic_id + URL_COMIC_THUMBNAIL_POSTFIX,
        feed_url=request.url,
        url=URL_GENRE,
        entries=atom_items
    )

    return atom.get_response()


@app.route('/lezhin-rss/')
def index():
    return index_p(1)


@app.route('/lezhin-rss/<int:page>')
def index_p(page):
    if page < 1:
        return redirect(url_for('index_p', page=1))
    context = dict()
    context['URL_COMIC_PREFIX'] = URL_COMIC_PREFIX
    context['URL_COMIC_THUMBNAIL_PREFIX'] = URL_COMIC_THUMBNAIL_PREFIX
    context['URL_COMIC_THUMBNAIL_POSTFIX'] = URL_COMIC_THUMBNAIL_POSTFIX
    context['comicrows'] = []
    context['page'] = page
    context['last_update'] = Comic.query.order_by(desc(Comic.last_updated)).first().last_updated.strftime(
        "%Y-%m-%d %H:%M:%S")

    query = Comic.query.order_by(Comic.title)

    context['q'] = None
    if 'q' in request.args:
        q = request.args.get('q')
        if q:
            context['q'] = q
            query = query.filter(or_(Comic.title.contains(q), Comic.artist_display_name.contains(q)))

    pagination = query.order_by(Comic.title).paginate(page, INDEX_PAGE_SIZE, False)

    if len(pagination.items) == 0 and pagination.has_prev:
        return redirect(url_for('index_p', page=pagination.total / INDEX_PAGE_SIZE + 1))

    context['has_next'] = pagination.has_next
    context['has_prev'] = pagination.has_prev

    comics = pagination.items

    for i in xrange(len(comics)):
        if i % INDEX_ITEM_IN_ROW == 0:
            context['comicrows'].append(list())
        context['comicrows'][i / INDEX_ITEM_IN_ROW].append(comics[i])

    return render_template('index.html', context=context)


@app.route('/lezhin-rss/api/comics')
def api_comics():
    comics = Comic.query.all()
    result = dict()
    result['comics'] = [json.loads(comic.original_json) for comic in comics]
    return json.dumps(result)


@app.route('/lezhin-rss/api/episodes/<string:comic_id>')
def api_episodes(comic_id):
    comic = Comic.query.get(comic_id)
    result = dict()
    if comic is None:
        result['status'] = "not found"
        result['episodes'] = list()
        return json.dumps(result), 404
    result['status'] = 'ok'
    result['episodes'] = [json.loads(episode.original_json) for episode in comic.episodes]
    return json.dumps(result)