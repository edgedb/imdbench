import dataclasses
import datetime
import os.path
import pickle
import random
import re
import typing

from collections import OrderedDict

from words import TextGenerator
from names import NameGenerator


tgen = TextGenerator()
ngen = NameGenerator()


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


def random_gauss_int(mu, sigma, minval=-99_999, maxval=99_999):
    while True:
        res = round(random.gauss(mu, sigma))
        if minval <= res <= maxval:
            return res


class DataGenerator:
    def __init__(self, people=10_000, users=10_000, reviews=50_000, new=False,
                 path=None):
        self._pickle_name = f'mdb_{people}_{users}_{reviews}.pickle'
        if path is not None:
            self._pickle_name = f'{path}{self._pickle_name}'

        if not new and os.path.exists(self._pickle_name):
            # retrieve the pickled movie DB data
            with open(self._pickle_name, 'rb') as f:
                self.mdb = pickle.load(f)
                self.__lastnid = self.mdb['lastnid']

        else:
            self.__lastnid = 0
            self.generate_mdb(people, users, reviews)
            self.dump()

    def dump(self):
        # pickle generated data
        with open(self._pickle_name, 'wb') as f:
            # write the __lastnid, so that we can generate more
            # data consistently, if needed
            self.mdb['lastnid'] = self.__lastnid
            pickle.dump(self.mdb, f)

    @property
    def nid(self):
        '''Automatically incrementing numerical ID.'''
        self.__lastnid += 1
        return self.__lastnid

    def get_image(self, name, nid):
        '''Given a string produce a plausible image file name.'''
        img = re.sub(r'(?i)\W+', '_', name)
        return f'{img}_{nid}.jpeg'

    def generate_mdb(self, num_people, num_users, num_reviews):
        self.mdb = {'movies': {}, 'people': {}, 'users': {}, 'reviews': {}}

        # generate people first
        self.generate_people(num_people)
        self.generate_directors(num_people)

        # clean up movies
        movies = self.mdb['movies']
        for m in movies.values():
            od = OrderedDict((p, 1) for p in m.cast)
            if len(m.cast) != len(od):
                # have duplicate entries
                m.cast = [p for p in od.keys()]

            od = OrderedDict((p, 1) for p in m.directors)
            if len(m.directors) != len(od):
                # have duplicate entries
                m.directors = [p for p in od.keys()]

        self.generate_users(num_users)
        self.generate_reviews(num_reviews)

    def generate_people(self, num_people):
        people = self.mdb['people']
        for i in range(num_people):
            person = self.new_person()
            people[person.nid] = person

        return people

    def new_person(self):
        full_name = ngen.get_full_name(as_list=True)
        fn, *mnid, ln = full_name
        nid = self.nid

        return Person(
            nid=nid,
            first_name=fn,
            middle_name=' '.join(mnid),
            last_name=ln,
            image=self.get_image(' '.join(full_name), nid),
            bio=tgen.generate_text(
                maxwords=random_gauss_int(20, 20, minval=10, maxval=50))
        )

    def get_acting_career(self):
        'A number of movies an actor starred in.'
        return max(1, round(random.expovariate(1 / 9)))

    def generate_directors(self, num_people):
        people = self.mdb['people']
        movies = self.mdb['movies']
        # some of the people will be directors, the rest - actors
        directors = {}
        # actor_pool is composed of all non-directors and some directors
        actor_pool = {}

        for i, person in enumerate(people.values()):
            if i < round(num_people * 0.07):
                # about 7% are directors
                directors[person.nid] = person

                if random.random() < 0.15:
                    # about 15% of them are also actors
                    actor_pool[person.nid] = (person, self.get_acting_career())
            else:
                # regular actors
                actor_pool[person.nid] = (person, self.get_acting_career())

        for director in directors.values():
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
                    st = tgen.generate_title(2)
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
                    title = tgen.generate_title(
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
                    description=tgen.generate_text(
                        maxwords=random.randint(50, 100)),
                    year=round(year),
                    directors=[director.nid],
                    cast=cast,
                    image=self.get_image(title, mnid)
                )
                # advance year
                year += min(max_delay, random.randint(1, round(max_delay + 1)))

                mov.append(m)
                movies[m.nid] = m

        # if there are actors left over in the pool, distribute them
        # among movies
        for actor_nid in actor_pool:
            actor, n = actor_pool[actor_nid]
            m_nids = random.sample(list(movies.keys()), min(n, len(movies)))
            for nid in m_nids:
                if actor.nid not in movies[nid].cast:
                    movies[nid].cast.append(actor.nid)

        # some movies have 2 directors
        for nid in random.sample(
                list(movies.keys()),
                round(len(movies) * 0.05)):
            movie = movies[nid]
            while True:
                new_dir = random.choice(list(directors.keys()))
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
                actor, n = actor_pool[nid]
                n -= 1
                if n == 0:
                    del actor_pool[nid]
                else:
                    actor_pool[nid] = (actor, n)

        return cast

    def generate_users(self, num_users):
        users = self.mdb['users']
        unames = set()

        for i in range(num_users):
            uname = ngen.get_first_name()
            nid = self.nid

            if uname in unames:
                uname += str(nid)

            unames.add(uname)
            user = User(
                nid=nid,
                name=uname,
                image=f'{uname.lower()}.jpeg'
            )
            users[nid] = user

        return users

    def generate_reviews(self, num_reviews):
        users = self.mdb['users']
        reviews = self.mdb['reviews']
        movies = self.mdb['movies']
        # 5 year period within which reviews will be spread
        delta = int(datetime.timedelta(days=365 * 5).total_seconds() / 60)
        avg = num_reviews / len(users)

        for unid, uname in users.items():
            mnids = random.sample(
                movies.keys(),
                min(random_gauss_int(avg, 4, minval=1, maxval=20), len(movies))
            )
            for mnid in mnids:
                tstamp = datetime.datetime.now() - datetime.timedelta(
                    minutes=random.randint(0, delta))
                r = random_gauss_int(3.5, 1.5, minval=0, maxval=5)
                body_length = random_gauss_int(5, 30, minval=1, maxval=100)
                body = tgen.generate_text(
                    maxwords=body_length if body_length < 100 else 1000)
                nid = self.nid
                reviews[nid] = Review(
                    nid=nid,
                    body=body,
                    rating=r,
                    author_nid=unid,
                    movie_nid=mnid,
                    creation_time=tstamp,
                )
