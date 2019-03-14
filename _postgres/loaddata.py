import asyncio
import progress.bar

import asyncpg

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
        con = await asyncpg.connect(
            user='postgres_bench', database='postgres_bench',
            password='edgedbbenchmark')

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
            else:
                bar.next()


async def import_data(data: dict):
    concurrency = 32

    users = data['users']
    reviews = data['reviews']
    movies = data['movies']
    people = data['people']

    users_data = [
        (
            lambda id, image=u.image: map_image(id, image),
            '''
            INSERT INTO users(name, image) VALUES ($1, $2) RETURNING id;
            ''',
            u.name,
            u.image,
        ) for u in users.values()
    ]

    movies_data = [
        (
            lambda id, image=m.image: map_image(id, image),
            '''
            INSERT INTO movies(image, title, year, description)
            VALUES ($1, $2, $3, $4) RETURNING id;
            ''',
            m.image,
            m.title,
            m.year,
            m.description,
        ) for m in movies.values()
    ]

    people_data = [
        (
            lambda id, image=p.image: map_image(id, image),
            '''
            INSERT INTO persons(first_name, middle_name, last_name, image, bio)
            VALUES ($1, $2, $3, $4, $5) RETURNING id;
            ''',
            p.first_name,
            p.middle_name,
            p.last_name,
            p.image,
            p.bio
        ) for p in people.values()
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
            None,
            image2id[people[d].image],
            image2id[m.image],
        ) for m in movies.values() for d in m.directors
    ]

    actors_data = [
        (
            None,
            '''
            INSERT INTO actors(list_order, person_id, movie_id)
            VALUES ($1, $2, $3);
            ''',
            ci if m.nid % 10 else None,
            image2id[people[c].image],
            image2id[m.image],
        ) for m in movies.values() for ci, c in enumerate(m.cast)
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
            r.body,
            r.rating,
            r.creation_time,
            image2id[users[r.author_nid].image],
            image2id[movies[r.movie_nid].image],
        ) for r in reviews.values()
    ]

    await Pool.map(reviews_data, concurrency=concurrency, label='reviews')


image2id = {}


def map_image(id, image):
    assert image not in image2id
    image2id[image] = id


if __name__ == '__main__':
    asyncio.run(import_data(dataset.load()))
