#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import json
import random
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.ext import baked
import _sqlalchemy.models as m


engine = None
session_factory = None
bakery = baked.bakery()
INSERT_PREFIX = 'insert_test__'


def connect(ctx):
    global engine
    global session_factory

    if session_factory is None:
        engine = sa.create_engine(
            f'postgresql://sqlalch_bench:edgedbbenchmark@'
            f'{ctx.db_host}:{ctx.pg_port}/sqlalch_bench')
        session_factory = orm.sessionmaker(bind=engine, expire_on_commit=False)

    return session_factory()


def close(ctx, sess):
    sess.close()


def load_ids(ctx, sess):
    users = (
        sess.query(m.User)
        .order_by(sa.func.random())
        .limit(ctx.number_of_ids)
    ).all()

    movies = (
        sess.query(m.Movie)
        .order_by(sa.func.random())
        .limit(ctx.number_of_ids)
    ).all()

    people = (
        sess.query(m.Person)
        .order_by(sa.func.random())
        .limit(ctx.number_of_ids)
    ).all()

    return dict(
        get_user=[u.id for u in users],
        get_movie=[m.id for m in movies],
        get_person=[p.id for p in people],
        # re-use user IDs for update tests
        update_movie=[m.id for m in movies],
        # generate as many insert stubs as "concurrency" to
        # accommodate concurrent inserts
        insert_user=[INSERT_PREFIX] * ctx.concurrency,
        insert_movie=[{
            'prefix': INSERT_PREFIX,
            'people': [p.id for p in people[:4]],
        }] * ctx.concurrency,
        insert_movie_plus=[INSERT_PREFIX] * ctx.concurrency,
    )


def get_user(sess, id):
    user_query = bakery(lambda sess: sess.query(m.User))
    user_query += lambda q: q.filter_by(id=sa.bindparam('id'))
    user = user_query(sess).params(id=id).first()

    latest_reviews = user.latest_reviews.options(
        orm.joinedload(m.Review.movie)).limit(10).all()

    result = json.dumps({
        'id': user.id,
        'name': user.name,
        'image': user.image,
        'latest_reviews': [
            {
                'id': r.id,
                'body': r.body,
                'rating': r.rating,
                'movie': {
                    'id': r.movie.id,
                    'image': r.movie.image,
                    'title': r.movie.title,
                    'avg_rating': float(r.movie.avg_rating),
                }
            } for r in latest_reviews
        ]
    })
    return result


def get_movie(sess, id):
    # to implement NULLS LAST use a numeric value larger than any
    # list order we can get from the DB
    NULLS_LAST = 2 ^ 64

    def sort_key(rel):
        if rel.list_order is None:
            return (NULLS_LAST, rel.person_rel.last_name)
        else:
            return (rel.list_order, rel.person_rel.last_name)

    baked_query = bakery(lambda sess: (
        sess.query(m.Movie)
            .options(
                orm.subqueryload(m.Movie.directors_rel)
                .joinedload(m.Directors.person_rel, innerjoin=True),

                orm.subqueryload(m.Movie.cast_rel)
                .joinedload(m.Cast.person_rel, innerjoin=True),

                orm.subqueryload(m.Movie.reviews)
                .joinedload(m.Review.author, innerjoin=True),
            )
        )
    )

    baked_query += lambda q: q.filter_by(id=sa.bindparam('id'))

    movie = baked_query(sess).params(id=id).first()

    directors = [rel.person_rel for rel in
                 sorted(movie.directors_rel, key=sort_key)]

    cast = [rel.person_rel for rel in
            sorted(movie.cast_rel, key=sort_key)]

    result = {
        'id': movie.id,
        'image': movie.image,
        'title': movie.title,
        'year': movie.year,
        'description': movie.description,
        'avg_rating': float(movie.avg_rating),
        'directors': [
            {
                'id': d.id,
                'full_name': d.full_name,
                'image': d.image,
            } for d in directors
        ],
        'cast': [
            {
                'id': c.id,
                'full_name': c.full_name,
                'image': c.image,
            } for c in cast
        ],
        'reviews': [
            {
                'id': r.id,
                'body': r.body,
                'rating': float(r.rating),
                'author': {
                    'id': r.author.id,
                    'name': r.author.name,
                    'image': r.author.image,
                }
            } for r in sorted(movie.reviews,
                              key=lambda x: x.creation_time,
                              reverse=True)
        ]
    }

    return json.dumps(result)


def get_person(sess, id):
    baked_query = bakery(lambda sess: sess.query(m.Person).options(
        orm.joinedload(m.Person.acted_in),
        orm.joinedload(m.Person.directed),
    ))

    baked_query += lambda q: q.filter_by(id=sa.bindparam('id'))

    person = baked_query(sess).params(id=id).first()

    result = {
        'id': person.id,
        'image': person.image,
        'full_name': person.full_name,
        'bio': person.bio,
        'acted_in': [
            {
                'id': m.id,
                'image': m.image,
                'title': m.title,
                'year': m.year,
                'avg_rating': float(m.avg_rating),
            } for m in sorted(person.acted_in,
                              key=lambda x: (x.year, x.title))
        ],
        'directed': [
            {
                'id': m.id,
                'image': m.image,
                'title': m.title,
                'year': m.year,
                'avg_rating': float(m.avg_rating),
            } for m in sorted(person.directed,
                              key=lambda x: (x.year, x.title))
        ],
    }

    return json.dumps(result)


def update_movie(sess, id):
    stmt = sa.update(
        m.Movie
    ).filter_by(
        id=sa.bindparam('m_id')
    ).values(
        title=m.Movie.title + sa.bindparam('suffix')
    ).returning(
        m.Movie.id,
        m.Movie.title,
    )

    result = sess.execute(
        stmt,
        dict(m_id=id, suffix=f'---{str(id)[:8]}')
    ).first()
    # Without this commit, the changes end up being committed outside
    # of where they are timed.
    sess.commit()

    return json.dumps({
        'id': result[0],
        'title': result[1],
    })


def insert_user(sess, val):
    num = random.randrange(1_000_000)
    user = m.User(name=f'{val}{num}', image=f'image_{val}{num}')
    sess.add(user)
    sess.commit()

    return json.dumps({
        'id': user.id,
        'name': user.name,
        'image': user.image,
    })


def insert_movie(sess, val):
    num = random.randrange(1_000_000)
    movie = m.Movie(
        title=f'{val["prefix"]}{num}',
        image=f'{val["prefix"]}image{num}.jpeg',
        description=f'{val["prefix"]}description{num}',
        year=num,
    )
    sess.add(movie)
    sess.commit()

    directors = m.Directors(person_id=val["people"][0], movie_id=movie.id)
    sess.add(directors)
    c0 = m.Cast(person_id=val["people"][1], movie_id=movie.id)
    c1 = m.Cast(person_id=val["people"][2], movie_id=movie.id)
    c2 = m.Cast(person_id=val["people"][3], movie_id=movie.id)
    sess.add(c0)
    sess.add(c1)
    sess.add(c2)
    sess.commit()

    result = {
        'id': movie.id,
        'image': movie.image,
        'title': movie.title,
        'year': movie.year,
        'description': movie.description,
        'directors': [
            {
                'id': directors.person_rel.id,
                'full_name': directors.person_rel.full_name,
                'image': directors.person_rel.image,
            }
        ],
        'cast': [
            {
                'id': c.person_rel.id,
                'full_name': c.person_rel.full_name,
                'image': c.person_rel.image,
            } for c in [c0, c1, c2]
        ],
    }
    return json.dumps(result)


def insert_movie_plus(sess, val):
    num = random.randrange(1_000_000)
    director = m.Person(
        first_name=f'{val}Alice',
        last_name=f'{val}Director',
        image=f'{val}image{num}.jpeg',
        bio='',
    )
    c0 = m.Person(
        first_name=f'{val}Billie',
        last_name=f'{val}Actor',
        image=f'{val}image{num+1}.jpeg',
        bio='',
    )
    c1 = m.Person(
        first_name=f'{val}Cameron',
        last_name=f'{val}Actor',
        image=f'{val}image{num+2}.jpeg',
        bio='',
    )
    sess.add(director)
    sess.add(c0)
    sess.add(c1)
    movie = m.Movie(
        title=f'{val}{num}',
        image=f'{val}image{num}.jpeg',
        description=f'{val}description{num}',
        year=num,
    )
    sess.add(movie)
    sess.commit()

    sess.add(m.Directors(person_id=director.id, movie_id=movie.id))
    sess.add(m.Cast(person_id=c0.id, movie_id=movie.id))
    sess.add(m.Cast(person_id=c1.id, movie_id=movie.id))
    sess.commit()

    result = {
        'id': movie.id,
        'image': movie.image,
        'title': movie.title,
        'year': movie.year,
        'description': movie.description,
        'directors': [
            {
                'id': director.id,
                'full_name': director.full_name,
                'image': director.image,
            }
        ],
        'cast': [
            {
                'id': c.id,
                'full_name': c.full_name,
                'image': c.image,
            } for c in [c0, c1]
        ],
    }
    return json.dumps(result)


def setup(ctx, sess, queryname):
    if queryname == 'update_movie':
        sess.query(
            m.Movie
        ).update(
            dict(title=sa.func.split_part(m.Movie.title, '---', 1))
        )
        sess.commit()
    elif queryname == 'insert_user':
        sess.query(
            m.User
        ).filter(
            m.User.name.like(f'{INSERT_PREFIX}%')
        ).delete(synchronize_session=False)
        sess.commit()
    elif queryname in {'insert_movie', 'insert_movie_plus'}:
        # XXX: I just gave up on trying to figure out how to bulk delete
        # all this in SQLAlchemy proper. Trying to filter the
        # relationships based on the Movie they target didn't seem to
        # work. So I'll use a raw query.
        sess.execute('''
            DELETE FROM
                "directors" as D
            USING
                "movie" as M
            WHERE
                D.movie_id = M.id AND M.image LIKE 'insert_test__%';

            DELETE FROM
                "cast" as C
            USING
                "movie" as M
            WHERE
                C.movie_id = M.id AND M.image LIKE 'insert_test__%';

            DELETE FROM
                "movie" as M
            WHERE
                M.image LIKE 'insert_test__%';

            DELETE FROM
                "person" as P
            WHERE
                P.image LIKE 'insert_test__%';
        ''')
        sess.commit()


def cleanup(ctx, sess, queryname):
    if queryname in {'update_movie', 'insert_user', 'insert_movie',
                     'insert_movie_plus'}:
        # The clean up is the same as setup for mutation benchmarks
        setup(ctx, sess, queryname)
