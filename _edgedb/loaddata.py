#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import asyncio
import edgedb
import progress.bar

import dataset


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
        con = await edgedb.async_connect(
            user='edgedb', database='edgedb_bench')

        try:
            while True:
                piece = await self._queue.get()
                if piece is self._STOP:
                    self._results.put_nowait(self._STOP)
                    break

                args, kwargs = piece
                try:
                    await con.fetchall(*args, **kwargs)
                except Exception as e:
                    self._results.put_nowait(e)
                else:
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

    users = data['users']
    reviews = data['reviews']
    movies = data['movies']
    people = data['people']

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
                first_name=p.first_name,
                middle_name=p.middle_name,
                last_name=p.last_name,
                image=p.image,
                bio=p.bio
            )
        ) for p in people.values()
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
                name=u.name,
                image=u.image,
            )
        ) for u in users.values()
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
                    if m.nid % 10 else movies_unord_insert_query),
            ),
            dict(
                title=m.title,
                description=m.description,
                year=m.year,
                image=m.image,
                directors=nid2image(people, m.directors),
                cast=nid2image(people, m.cast),
            )
        ) for m in movies.values()
    ]

    reviews_insert_query = r'''
        INSERT Review {
            body := <str>$body,
            rating := <int64>$rating,
            author := (SELECT User FILTER .image = <str>$uimage LIMIT 1),
            movie := (SELECT Movie FILTER .image = <str>$mimage LIMIT 1),
            creation_time := <local_datetime>$creation_time,
        };
    '''

    reviews_data = [
        (
            (reviews_insert_query,),
            dict(
                body=r.body,
                rating=r.rating,
                uimage=users[r.author_nid].image,
                mimage=movies[r.movie_nid].image,
                creation_time=r.creation_time,
            )
        ) for r in reviews.values()
    ]

    await Pool.map(people_data, concurrency=concurrency, label='people')
    await Pool.map(users_data, concurrency=concurrency, label='users')
    await Pool.map(movies_data, concurrency=concurrency, label='movies')
    await Pool.map(reviews_data, concurrency=concurrency, label='reviews')


def nid2image(items, nids):
    result = []
    for nid in nids:
        result.append(items[nid].image)

    return result


if __name__ == '__main__':
    asyncio.run(import_data(dataset.load()))
