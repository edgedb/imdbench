#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import dataclasses
import datetime
import gzip
import pathlib
import pickle
import random
import re
import typing

import progress.bar

from . import textgen
from . import namegen


BUILD_PATH = pathlib.Path(__file__).resolve().parent / 'build'
DATASET_PATH = BUILD_PATH / 'dataset.pickle.gz'


@dataclasses.dataclass
class Person:
    nid: int  # numeric id, used to relate data before it is dumped into DB
    first_name: str
    middle_name: str
    last_name: str
    image: str
    bio: str


@dataclasses.dataclass
class Movie:
    nid: int
    title: str
    description: str
    year: int
    image: str

    directors: typing.List[int]
    cast: typing.List[int]


@dataclasses.dataclass
class User:
    nid: int
    name: str
    image: str


@dataclasses.dataclass
class Review:
    nid: int
    body: str
    rating: int
    author_nid: int
    movie_nid: int
    creation_time: datetime.datetime


def load():
    with gzip.open(DATASET_PATH, 'rb') as f:
        return pickle.loads(f.read())


def random_gauss_int(mu, sigma, minval=-99_999, maxval=99_999):
    while True:
        res = round(random.gauss(mu, sigma))
        if minval <= res <= maxval:
            return res


def bar(label, it, total):
    return progress.bar.Bar(label[:30].ljust(30), max=total).iter(it)


class DataGenerator:

    tgen = None
    ngen = None

    def __init__(self, people: int, users: int, reviews: int):
        self.num_people = people
        self.num_users = users
        self.num_reviews = reviews

        self.__lastnid = 0
        self._init_gens()

    @classmethod
    def _init_gens(cls):
        if cls.tgen is None:
            cls.tgen = textgen.TextGenerator()
        if cls.ngen is None:
            cls.ngen = namegen.NameGenerator()

    def dump(self):
        data = pickle.dumps(self.mdb)
        with gzip.open(DATASET_PATH, 'wb') as f:
            f.write(data)

    @property
    def nid(self):
        '''Automatically incrementing numerical ID.'''
        self.__lastnid += 1
        return self.__lastnid

    def generate_mdb(self):
        self.mdb = {'movies': {}, 'people': {}, 'users': {}, 'reviews': {}}

        # generate people first
        self.generate_people()
        self.generate_directors()

        # clean up movies
        movies = self.mdb['movies']
        for m in movies.values():
            od = {p: 1 for p in m.cast}
            if len(m.cast) != len(od):
                # have duplicate entries
                m.cast = [p for p in od.keys()]

            od = {p: 1 for p in m.directors}
            if len(m.directors) != len(od):
                # have duplicate entries
                m.directors = [p for p in od.keys()]

        self.generate_users()
        self.generate_reviews()

        self.populate_details()

    def generate_people(self):
        people = self.mdb['people']
        for i in bar('Actors', range(self.num_people), self.num_people):
            # for now just fill in the nid for the objects
            people[self.nid] = True

        return people

    def get_acting_career(self):
        'A number of movies an actor starred in.'
        return max(1, round(random.expovariate(1 / 9)))

    def generate_directors(self):
        people = self.mdb['people']
        movies = self.mdb['movies']
        # some of the people will be directors, the rest - actors
        directors = set()
        # actor_pool is composed of all non-directors and some directors
        actor_pool = {}

        for i, person_nid in enumerate(people.keys()):
            if i < round(self.num_people * 0.07):
                # about 7% are directors
                directors.add(person_nid)

                if random.random() < 0.15:
                    # about 15% of them are also actors
                    actor_pool[person_nid] = self.get_acting_career()
            else:
                # regular actors
                actor_pool[person_nid] = self.get_acting_career()

        for director_nid in bar('Directors & Movies',
                                directors, len(directors)):
            # what makes directors special is that they make movies
            num_movies = max(1, round(random.expovariate(1 / 3.5)))
            career_start = max(1950, 2018 - num_movies - random.randint(0, 70))
            max_delay = (2018 - career_start) / num_movies

            mov = []
            year = career_start
            series_titles = []
            series_wishlist = []
            for i in range(num_movies):
                # always a chance to start a series
                if not series_titles and random.random() < 0.08:
                    st = self.tgen.generate_title(2)
                    series_wishlist = random.sample(
                        list(actor_pool.keys()),
                        k=random_gauss_int(10, 10, 1, 100)
                    )
                    for n in range(random.randint(2, 4)):
                        if n == 0:
                            series_titles.append(st)
                        else:
                            series_titles.append(st + f' {n + 1}')

                # title generation for series is different
                if series_titles:
                    title = series_titles.pop(0)
                    cast = self.get_cast(actor_pool, series_wishlist)
                else:
                    title = self.tgen.generate_title(
                        random_gauss_int(2, 1.5, 1, 10))
                    # figure out the movie cast

                    cast = self.get_cast(actor_pool, random.sample(
                        list(actor_pool.keys()),
                        min(random_gauss_int(10, 10, 1, 100), len(actor_pool))
                    ))

                mnid = self.nid
                m = Movie(
                    nid=self.nid,
                    title=title.title(),
                    description=self.tgen.generate_text(
                        maxwords=random.randint(50, 100)),
                    year=round(year),
                    directors=[director_nid],
                    cast=cast,
                    image=get_image(title, mnid)
                )
                # advance year
                year += min(max_delay, random.randint(1, round(max_delay + 1)))

                mov.append(m)
                movies[m.nid] = m

        # if there are actors left over in the pool, distribute them
        # among movies
        for actor_nid, n in actor_pool.items():
            m_nids = random.sample(list(movies.keys()), min(n, len(movies)))
            for nid in m_nids:
                if actor_nid not in movies[nid].cast:
                    movies[nid].cast.append(actor_nid)

        directors_list = list(directors)
        # some movies have 2 directors
        for nid in random.sample(
                list(movies.keys()),
                round(len(movies) * 0.05)):
            movie = movies[nid]
            while True:
                new_dir = random.choice(directors_list)
                if new_dir not in movie.directors:
                    movie.directors.append(new_dir)
                break

        return directors

    def get_cast(self, actor_pool, wishlist):
        # figure out the movie cast
        cast = []
        for nid in wishlist:
            if nid in actor_pool:
                cast.append(nid)
                n = actor_pool[nid]
                n -= 1
                if n == 0:
                    del actor_pool[nid]
                else:
                    actor_pool[nid] = n

        return cast

    def generate_users(self):
        users = self.mdb['users']
        for i in bar('Users', range(self.num_users), self.num_users):
            users[self.nid] = True

        return users

    def generate_reviews(self):
        users = self.mdb['users']
        reviews = self.mdb['reviews']
        movies = self.mdb['movies']
        movie_nids = list(movies.keys())
        avg = self.num_reviews / len(users)

        for unid in bar('User reviews', users.keys(), len(users)):
            mnids = random.sample(
                movie_nids,
                min(random_gauss_int(avg, 4, minval=1, maxval=20), len(movies))
            )
            for mnid in mnids:
                nid = self.nid
                reviews[nid] = (unid, mnid)

    def update_users(self):
        users = self.mdb['users']
        unames = set()

        for user in bar('reconciling usernames', users.values(), len(users)):
            uname = user.name

            if uname in unames:
                uname += str(user.nid)
                # update the name and image
                user.name = uname
                user.image = f'{uname.lower()}.jpeg'

            unames.add(uname)

    def populate_details(self):
        people = self.mdb['people']
        users = self.mdb['users']
        reviews = self.mdb['reviews']

        people_nids = list(people.keys())
        users_nids = list(users.keys())
        reviews_nids = list(reviews.keys())

        kwargs = dict(ngen=self.ngen, tgen=self.tgen)

        for nid in bar('generating person details',
                       people_nids, len(people_nids)):
            people[nid] = populate_person(nid, **kwargs)

        for nid in bar('generating user details',
                       users_nids, len(users_nids)):
            users[nid] = populate_user(nid, **kwargs)

        # 5 year period within which reviews will be spread
        delta = int(datetime.timedelta(days=365 * 5).total_seconds() / 60)
        for nid in bar('generating review details',
                       reviews_nids, len(reviews_nids)):
            unid, mnid = reviews[nid]
            reviews[nid] = populate_review(nid, unid, mnid, delta, **kwargs)

        self.update_users()


def get_image(name, nid):
    '''Given a string produce a plausible image file name.'''
    img = re.sub(r'(?i)\W+', '_', name)
    return f'{img}_{nid}.jpeg'


def populate_person(nid, *, ngen, tgen):
    full_name = ngen.get_full_name(as_list=True)
    fn, *middle, ln = full_name

    return Person(
        nid=nid,
        first_name=fn,
        middle_name=' '.join(middle),
        last_name=ln,
        image=get_image(' '.join(full_name), nid),
        bio=tgen.generate_text(
                maxwords=random_gauss_int(20, 20, minval=10, maxval=50)),
    )


def populate_user(nid, *, ngen, tgen):
    uname = ngen.get_first_name()

    return User(
        nid=nid,
        name=uname,
        image=f'{uname.lower()}.jpeg',
    )


def populate_review(nid, unid, mnid, delta, *, ngen, tgen):
    body_length = random_gauss_int(5, 30, minval=1, maxval=100)

    return Review(
        nid=nid,
        body=tgen.generate_text(
            maxwords=body_length if body_length < 100 else 1000),
        rating=random_gauss_int(3.5, 1.5, minval=0, maxval=5),
        author_nid=unid,
        movie_nid=mnid,
        creation_time=datetime.datetime.now() - datetime.timedelta(
            minutes=random.randint(0, delta)),
    )
