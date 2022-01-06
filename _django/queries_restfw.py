#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


from django.db import connection
from django.test.client import RequestFactory
import json
import random

from . import bootstrap  # NoQA

from . import models
from . import views


rf = RequestFactory()
DUMMY_REQUEST = rf.get('/')
USER_VIEW = views.UserDetailsViewSet.as_view({'get': 'retrieve'})
MOVIE_VIEW = views.MovieDetailsViewSet.as_view({'get': 'retrieve'})
PERSON_VIEW = views.PersonDetailsViewSet.as_view({'get': 'retrieve'})
MOVIE_UPDATE_VIEW = views.MovieUpdateViewSet.as_view({'post': 'update'})
USER_INSERT_VIEW = views.UserInsertViewSet.as_view({'post': 'create'})
INSERT_PREFIX = 'insert_test__'


def init(ctx):
    from django.conf import settings
    settings.DATABASES["default"]["HOST"] = ctx.db_host


def connect(ctx):
    # Django fully abstracts away connection management, so we
    # rely on it to create a new connection for every benchmark
    # thread.
    return None


def close(ctx, db):
    return


def load_ids(ctx, db):
    users = models.User.objects.raw('''
        SELECT * FROM _django_user ORDER BY random() LIMIT %s
    ''', [ctx.number_of_ids])

    movies = models.Movie.objects.raw('''
        SELECT * FROM _django_movie ORDER BY random() LIMIT %s
    ''', [ctx.number_of_ids])

    people = models.Person.objects.raw('''
        SELECT * FROM _django_person ORDER BY random() LIMIT %s
    ''', [ctx.number_of_ids])

    return dict(
        get_user=[d.id for d in users],
        get_movie=[d.id for d in movies],
        get_person=[d.id for d in people],
        # re-use user IDs for update tests
        update_movie=[d.id for d in movies],
        # generate as many insert stubs as "concurrency" to
        # accommodate concurrent inserts
        insert_user=[INSERT_PREFIX] * ctx.concurrency,
        insert_movie=[{
            'prefix': INSERT_PREFIX,
            'people': [p.id for p in people[:4]],
        }] * ctx.concurrency,
        insert_movie_plus=[INSERT_PREFIX] * ctx.concurrency,
    )


def get_user(conn, id):
    return USER_VIEW(DUMMY_REQUEST, pk=id).render().getvalue()


def get_movie(conn, id):
    return MOVIE_VIEW(DUMMY_REQUEST, pk=id).render().getvalue()


def get_person(conn, id):
    return PERSON_VIEW(DUMMY_REQUEST, pk=id).render().getvalue()


def update_movie(conn, id):
    return MOVIE_UPDATE_VIEW(
        rf.post('/', data={'title': f'---{id}'}),
        pk=id
    ).render().getvalue()


def insert_user(conn, val):
    num = random.randrange(1_000_000)
    return USER_INSERT_VIEW(
        rf.post(
            '/',
            data={'name': f'{val}{num}', 'image': f'{val}image{num}'}
        )
    ).render().getvalue()


def insert_movie(conn, val):
    # copied from plain Django test, because it appears that the
    # nested insert would be customized similar to this anyway
    num = random.randrange(1_000_000)
    people = models.Person.objects.filter(pk__in=val['people']).all()
    movie = models.Movie.objects.create(
        title=f'{val["prefix"]}{num}',
        image=f'{val["prefix"]}image{num}.jpeg',
        description=f'{val["prefix"]}description{num}',
        year=num,
    )
    movie.directors.set(people[:1])
    movie.cast.set(people[1:])
    movie.save()

    return json.dumps(views.CustomMovieView.render(None, movie))


def insert_movie_plus(conn, val):
    # copied from plain Django test, because it appears that the
    # nested insert would be customized similar to this anyway
    num = random.randrange(1_000_000)

    director = models.Person.objects.create(
        first_name=f'{val}Alice',
        last_name=f'{val}Director',
        image=f'{val}image{num}.jpeg',
        bio='',
    )
    c0 = models.Person.objects.create(
        first_name=f'{val}Billie',
        last_name=f'{val}Actor',
        image=f'{val}image{num+1}.jpeg',
        bio='',
    )
    c1 = models.Person.objects.create(
        first_name=f'{val}Cameron',
        last_name=f'{val}Actor',
        image=f'{val}image{num+2}.jpeg',
        bio='',
    )
    movie = models.Movie.objects.create(
        title=f'{val}{num}',
        image=f'{val}image{num}.jpeg',
        description=f'{val}description{num}',
        year=num,
    )
    movie.directors.set([director])
    movie.cast.set([c0, c1])
    movie.save()

    return json.dumps(views.CustomMovieView.render(None, movie))


def setup(ctx, conn, queryname):
    if queryname == 'update_movie':
        with connection.cursor() as cur:
            cur.execute('''
                UPDATE
                    _django_movie
                SET
                    title = split_part(_django_movie.title, '---', 1)
                WHERE
                    _django_movie.title LIKE '%---%';
            ''')
    elif queryname == 'insert_user':
        with connection.cursor() as cur:
            cur.execute('''
                DELETE FROM
                    _django_user
                WHERE
                    _django_user.name LIKE %s
            ''', [f'{INSERT_PREFIX}%'])
    elif queryname in {'insert_movie', 'insert_movie_plus'}:
        with connection.cursor() as cur:
            cur.execute('''
                DELETE FROM
                    "_django_directors" as D
                USING
                    "_django_movie" as M
                WHERE
                    D.movie_id = M.id AND M.image LIKE %s;
            ''', [f'{INSERT_PREFIX}%'])
            cur.execute('''
                DELETE FROM
                    "_django_cast" as C
                USING
                    "_django_movie" as M
                WHERE
                    C.movie_id = M.id AND M.image LIKE %s;
            ''', [f'{INSERT_PREFIX}%'])
            cur.execute('''
                DELETE FROM
                    "_django_movie" as M
                WHERE
                    M.image LIKE %s;
            ''', [f'{INSERT_PREFIX}%'])
            cur.execute('''
                DELETE FROM
                    "_django_person" as P
                WHERE
                    P.image LIKE %s;
            ''', [f'{INSERT_PREFIX}%'])


def cleanup(ctx, conn, queryname):
    if queryname in {'update_movie', 'insert_user', 'insert_movie',
                     'insert_movie_plus'}:
        # The clean up is the same as setup for mutation benchmarks
        setup(ctx, conn, queryname)
