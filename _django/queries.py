#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import json

from . import bootstrap  # NoQA

from . import models
from . import views


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
    )


def get_user(conn, id):
    user = models.User.objects.get(pk=id)
    return json.dumps(views.CustomUserView.render(None, user))


def get_movie(conn, id):
    user = models.Movie.objects.get(pk=id)
    return json.dumps(views.CustomMovieView.render(None, user))


def get_person(conn, id):
    user = models.Person.objects.get(pk=id)
    return json.dumps(views.CustomPersonView.render(None, user))
