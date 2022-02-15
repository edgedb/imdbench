#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import argparse
import asyncio
import asyncpg
import collections
import datetime
import json
import progress.bar


class Pool:

    _STOP = object()

    def __init__(self, data, *, concurrency: int):
        self._concurrency = concurrency

        self._results = asyncio.Queue()

        self._queue = asyncio.Queue()
        for piece in data:
            self._queue.put_nowait(piece)
        for _ in range(self._concurrency):
            self._queue.put_nowait(self._STOP)

        self._workers = []

    def _start(self):
        for _ in range(self._concurrency):
            self._workers.append(
                asyncio.create_task(self._worker()))

    async def _worker(self):
        con = await asyncpg.connect(
            user='postgres_bench', database='postgres_bench',
            password='edgedbbenchmark', host='localhost', port=15432)

        try:
            while True:
                args = await self._queue.get()
                if args is self._STOP:
                    self._results.put_nowait(self._STOP)
                    break
                cb, *args = args

                try:
                    i = await con.fetchval(*args)
                except Exception as e:
                    self._results.put_nowait(e)
                else:
                    if cb is not None:
                        cb(i)
                    self._results.put_nowait(True)
        finally:
            await con.close()

    @classmethod
    async def map(cls, data, *, concurrency: int, label: str):
        pool = cls(data, concurrency=concurrency)
        pool._start()

        bar = progress.bar.Bar(label[:15].ljust(15), max=len(data))

        stop_cnt = 0
        while True:
            piece = await pool._results.get()
            if piece is cls._STOP:
                stop_cnt += 1
                if stop_cnt == concurrency:
                    bar.finish()
                    return
            elif isinstance(piece, Exception):
                raise piece
            else:
                bar.next()


async def import_data(data: dict):
    concurrency = 32

    users = data['user']
    reviews = data['review']
    movies = data['movie']
    people = data['person']

    users_data = [
        (
            lambda realid, origid=u['id']: map_ids(realid, origid, 'user'),
            '''
            INSERT INTO users(name, image) VALUES ($1, $2) RETURNING id;
            ''',
            u['name'],
            u['image'],
        ) for u in users
    ]

    movies_data = [
        (
            lambda realid, origid=m['id']: map_ids(realid, origid, 'movie'),
            '''
            INSERT INTO movies(image, title, year, description)
            VALUES ($1, $2, $3, $4) RETURNING id;
            ''',
            m['image'],
            m['title'],
            m['year'],
            m['description'],
        ) for m in movies
    ]

    people_data = [
        (
            lambda realid, origid=p['id']: map_ids(realid, origid, 'person'),
            '''
            INSERT INTO persons(first_name, middle_name, last_name, image, bio)
            VALUES ($1, $2, $3, $4, $5) RETURNING id;
            ''',
            p['first_name'],
            p['middle_name'],
            p['last_name'],
            p['image'],
            p['bio'],
        ) for p in people
    ]

    await Pool.map(users_data, concurrency=concurrency, label='users')
    await Pool.map(movies_data, concurrency=concurrency, label='movies')
    await Pool.map(people_data, concurrency=concurrency, label='people')

    directors_data = [
        (
            None,
            '''
            INSERT INTO directors(list_order, person_id, movie_id)
            VALUES ($1, $2, $3);
            ''',
            d['list_order'],
            ids_map['person'][d['person_id']],
            ids_map['movie'][d['movie_id']],
        ) for d in data['directors']
    ]

    actors_data = [
        (
            None,
            '''
            INSERT INTO actors(list_order, person_id, movie_id)
            VALUES ($1, $2, $3);
            ''',
            c.get('list_order', None),
            ids_map['person'][c['person_id']],
            ids_map['movie'][c['movie_id']],
        ) for c in data['cast']
    ]

    await Pool.map(directors_data, concurrency=concurrency, label='directors')
    await Pool.map(actors_data, concurrency=concurrency, label='actors')

    reviews_data = [
        (
            None,
            '''
            INSERT INTO
                reviews(body, rating, creation_time, author_id, movie_id)
            VALUES ($1, $2, $3, $4, $5);
            ''',
            r['body'],
            r['rating'],
            r['creation_time'],
            ids_map['user'][r['author_id']],
            ids_map['movie'][r['movie_id']],
        ) for r in reviews
    ]

    await Pool.map(reviews_data, concurrency=concurrency, label='reviews')


ids_map = {'person': {}, 'user': {}, 'movie': {}}


def map_ids(realid, origid, cat):
    assert origid not in ids_map[cat]
    ids_map[cat][origid] = realid


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Load a specific fixture, old data will be purged.')
    parser.add_argument('filename', type=str,
                        help='The JSON dataset file')

    args = parser.parse_args()

    with open(args.filename, 'rt') as f:
        records = json.load(f)

    data = collections.defaultdict(list)
    for rec in records:
        rtype = rec['model'].split('.')[-1]
        datum = rec['fields']
        if 'pk' in rec:
            datum['id'] = rec['pk']
        # convert datetime
        if rtype == 'review':
            datum['creation_time'] = datetime.datetime.fromisoformat(
                datum['creation_time'])

        data[rtype].append(datum)

    asyncio.run(import_data(data))
