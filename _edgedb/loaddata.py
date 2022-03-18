#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import argparse
import asyncio
import edgedb
import json
import progress.bar
import uvloop


class Pool:

    _STOP = object()

    def __init__(self, data, *, concurrency: int):
        self._concurrency = concurrency
        self.client = edgedb.create_async_client(max_concurrency=concurrency)

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
        try:
            while True:
                piece = await self._queue.get()
                if piece is self._STOP:
                    self._results.put_nowait(self._STOP)
                    break

                args, kwargs = piece
                try:
                    await self.client.query(*args, **kwargs)
                except Exception as e:
                    self._results.put_nowait(e)
                else:
                    self._results.put_nowait(True)
        finally:
            pass

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

        await pool.client.aclose()


async def import_data(data: dict):
    concurrency = 32

    users = data['user']
    reviews = data['review']
    movies = data['movie']
    people = data['person']

    id2image_maps = {}
    for cat in ['user', 'person', 'movie']:
        id2image_maps[cat] = {r['id']: r['image'] for r in data[cat]}

    ppl_insert_query = r'''
        INSERT Person {
            first_name := <str>$first_name,
            middle_name := <str>$middle_name,
            last_name := <str>$last_name,
            image := <str>$image,
            bio := <str>$bio,
        };
    '''

    people_data = [
        (
            (ppl_insert_query,),
            dict(
                first_name=p['first_name'],
                middle_name=p['middle_name'],
                last_name=p['last_name'],
                image=p['image'],
                bio=p['bio']
            )
        ) for p in people
    ]

    users_insert_query = r'''
        INSERT User {
            name := <str>$name,
            image := <str>$image,
        };
    '''

    users_data = [
        (
            (users_insert_query,),
            dict(
                name=u['name'],
                image=u['image'],
            )
        ) for u in users
    ]

    movies_ord_insert_query = r'''
        INSERT Movie {
            title := <str>$title,
            description := <str>$description,
            year := <int64>$year,
            image := <str>$image,

            directors := (
                FOR X IN {
                    enumerate(array_unpack(
                        <array<str>>$directors
                    ))
                }
                UNION (
                    SELECT Person {@list_order := X.0}
                    FILTER .image = X.1
                )
            ),
            cast := (
                FOR X IN {
                    enumerate(array_unpack(
                        <array<str>>$cast
                    ))
                }
                UNION (
                    SELECT Person {@list_order := X.0}
                    FILTER .image = X.1
                )
            )
        };
    '''

    movies_unord_insert_query = r'''
        INSERT Movie {
            title := <str>$title,
            description := <str>$description,
            year := <int64>$year,
            image := <str>$image,

            directors := (
                FOR X IN {
                    enumerate(array_unpack(
                        <array<str>>$directors
                    ))
                }
                UNION (
                    SELECT Person {@list_order := X.0}
                    FILTER .image = X.1
                )
            ),
            cast := (
                SELECT Person
                FILTER .image IN array_unpack(
                    <array<str>>$cast
                )
            )
        };
    '''

    movies_data = [
        (
            (
                (movies_ord_insert_query
                    if m['id'] % 10 else movies_unord_insert_query),
            ),
            dict(
                title=m['title'],
                description=m['description'],
                year=m['year'],
                image=m['image'],
                directors=id2image(id2image_maps['person'], m['directors']),
                cast=id2image(id2image_maps['person'], m['cast']),
            )
        ) for m in movies
    ]

    reviews_insert_query = r'''
        INSERT Review {
            body := <str>$body,
            rating := <int64>$rating,
            author := (SELECT User FILTER .image = <str>$uimage LIMIT 1),
            movie := (SELECT Movie FILTER .image = <str>$mimage LIMIT 1),
            creation_time := <cal::local_datetime><str>$creation_time,
        };
    '''

    reviews_data = [
        (
            (reviews_insert_query,),
            dict(
                body=r['body'],
                rating=r['rating'],
                uimage=id2image_maps['user'][r['author']],
                mimage=id2image_maps['movie'][r['movie']],
                creation_time=r['creation_time'][:-6],
            )
        ) for r in reviews
    ]

    await Pool.map(people_data, concurrency=concurrency, label='people')
    await Pool.map(users_data, concurrency=concurrency, label='users')
    await Pool.map(movies_data, concurrency=concurrency, label='movies')
    await Pool.map(reviews_data, concurrency=concurrency, label='reviews')


def id2image(idmap, ids):
    return [idmap[val] for val in ids]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Load EdgeDB dataset.')
    parser.add_argument('filename', type=str,
                        help='The JSON dataset file')
    args = parser.parse_args()

    with open(args.filename, 'rt') as f:
        records = json.load(f)

    uvloop.install()
    asyncio.run(import_data(records))
