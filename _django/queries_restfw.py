#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


from django.test.client import RequestFactory

from . import bootstrap  # NoQA

from . import models
from . import views


rf = RequestFactory()
DUMMY_REQUEST = rf.get('/')
USER_VIEW = views.UserDetailsViewSet.as_view({'get': 'retrieve'})
MOVIE_VIEW = views.MovieDetailsViewSet.as_view({'get': 'retrieve'})
PERSON_VIEW = views.PersonDetailsViewSet.as_view({'get': 'retrieve'})


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
    )


def get_user(conn, id):
    return USER_VIEW(DUMMY_REQUEST, pk=id).render().getvalue()


def get_movie(conn, id):
    return MOVIE_VIEW(DUMMY_REQUEST, pk=id).render().getvalue()


def get_person(conn, id):
    return PERSON_VIEW(DUMMY_REQUEST, pk=id).render().getvalue()
