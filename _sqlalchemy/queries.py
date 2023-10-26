#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import json
import os
import random
import sqlalchemy as sa
import sqlalchemy.orm as orm
import _sqlalchemy.models as m


engine = None
session_factory = None
INSERT_PREFIX = "insert_test__"


def connect(ctx):
    global engine
    global session_factory

    if session_factory is None:
        dsn = (
            f"postgresql://sqlalch_bench:edgedbbenchmark@"
            f"{ctx.db_host}:{ctx.pg_port}/sqlalch_bench"
        )
        if 'IMDBENCH_EXTRA_ENV' in os.environ:
            if os.environ['IMDBENCH_EXTRA_ENV'] == 'supabase':
                dsn = (
                    f"mysql://{os.environ['PLANETSCALE_USER']}:"
                    f"{os.environ['PLANETSCALE_PASSWORD']}@"
                    f"{os.environ['PLANETSCALE_HOST']}/"
                    f"{os.environ['PLANETSCALE_DATABASE']}"
                )
        engine = sa.create_engine(dsn)
        session_factory = orm.sessionmaker(bind=engine, expire_on_commit=False)

    return session_factory()


def close(ctx, sess):
    sess.close()
    sess.bind.dispose()


def load_ids(ctx, sess):
    users = sess.scalars(
        sa.select(m.User).order_by(sa.func.random()).limit(ctx.number_of_ids)
    ).all()

    movies = sess.scalars(
        sa.select(m.Movie).order_by(sa.func.random()).limit(ctx.number_of_ids)
    ).all()

    people = sess.scalars(
        sa.select(m.Person).order_by(sa.func.random()).limit(ctx.number_of_ids)
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
        insert_movie=[
            {
                "prefix": INSERT_PREFIX,
                "people": [p.id for p in people[:4]],
            }
        ]
        * ctx.concurrency,
        insert_movie_plus=[INSERT_PREFIX] * ctx.concurrency,
    )


def get_user(sess, id):
    user_query = sa.select(m.User).filter_by(id=id)
    user = sess.scalars(user_query).first()

    stmt = (
        sa.select(m.Review)
        .where(orm.with_parent(user, m.User.latest_reviews))
        .options(orm.joinedload(m.Review.movie))
        .limit(10)
    )
    latest_reviews = sess.scalars(stmt).all()

    result = json.dumps(
        {
            "id": user.id,
            "name": user.name,
            "image": user.image,
            "latest_reviews": [
                {
                    "id": r.id,
                    "body": r.body,
                    "rating": r.rating,
                    "movie": {
                        "id": r.movie.id,
                        "image": r.movie.image,
                        "title": r.movie.title,
                        "avg_rating": float(r.movie.avg_rating),
                    },
                }
                for r in latest_reviews
            ],
        }
    )
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

    stmt = (
        sa.select(m.Movie)
        .options(
            orm.selectinload(m.Movie.directors_rel).joinedload(m.Directors.person_rel),
            orm.selectinload(m.Movie.cast_rel).joinedload(m.Cast.person_rel),
            orm.selectinload(m.Movie.reviews).joinedload(m.Review.author),
        )
        .filter_by(id=id)
    )

    movie = sess.scalars(stmt).first()

    directors = [rel.person_rel for rel in sorted(movie.directors_rel, key=sort_key)]

    cast = [rel.person_rel for rel in sorted(movie.cast_rel, key=sort_key)]

    result = {
        "id": movie.id,
        "image": movie.image,
        "title": movie.title,
        "year": movie.year,
        "description": movie.description,
        "avg_rating": float(movie.avg_rating),
        "directors": [
            {
                "id": d.id,
                "full_name": d.full_name,
                "image": d.image,
            }
            for d in directors
        ],
        "cast": [
            {
                "id": c.id,
                "full_name": c.full_name,
                "image": c.image,
            }
            for c in cast
        ],
        "reviews": [
            {
                "id": r.id,
                "body": r.body,
                "rating": float(r.rating),
                "author": {
                    "id": r.author.id,
                    "name": r.author.name,
                    "image": r.author.image,
                },
            }
            for r in sorted(movie.reviews, key=lambda x: x.creation_time, reverse=True)
        ],
    }

    return json.dumps(result)


def get_person(sess, id):
    stmt = (
        sa.select(m.Person)
        .options(
            orm.selectinload(m.Person.acted_in),
            orm.selectinload(m.Person.directed),
        )
        .filter_by(id=id)
    )

    person = sess.scalars(stmt).first()

    result = {
        "id": person.id,
        "image": person.image,
        "full_name": person.full_name,
        "bio": person.bio,
        "acted_in": [
            {
                "id": m.id,
                "image": m.image,
                "title": m.title,
                "year": m.year,
                "avg_rating": float(m.avg_rating),
            }
            for m in sorted(person.acted_in, key=lambda x: (x.year, x.title))
        ],
        "directed": [
            {
                "id": m.id,
                "image": m.image,
                "title": m.title,
                "year": m.year,
                "avg_rating": float(m.avg_rating),
            }
            for m in sorted(person.directed, key=lambda x: (x.year, x.title))
        ],
    }

    return json.dumps(result)


def update_movie(sess, id):
    stmt = (
        sa.update(m.Movie)
        .filter_by(id=id)
        .values(title=m.Movie.title + f"---{str(id)[:8]}")
        .returning(
            m.Movie.id,
            m.Movie.title,
        )
    )

    result = sess.execute(stmt).first()
    # Without this commit, the changes end up being committed outside
    # of where they are timed.
    sess.commit()

    return json.dumps(
        {
            "id": result[0],
            "title": result[1],
        }
    )


def insert_user(sess, val):
    num = random.randrange(1_000_000)
    user = m.User(name=f"{val}{num}", image=f"image_{val}{num}")
    sess.add(user)
    sess.commit()

    return json.dumps(
        {
            "id": user.id,
            "name": user.name,
            "image": user.image,
        }
    )


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

    people = sess.scalars(
        sa.select(m.Person)
        .where(m.Person.id.in_(val["people"][0:4]))
        .order_by(m.Person.id)
    ).all()

    directors = m.Directors(person_rel=people[0], movie_id=movie.id)
    sess.add(directors)
    c0 = m.Cast(person_rel=people[1], movie_id=movie.id)
    c1 = m.Cast(person_rel=people[2], movie_id=movie.id)
    c2 = m.Cast(person_rel=people[3], movie_id=movie.id)

    sess.add_all([c0, c1, c2])

    sess.commit()
    result = {
        "id": movie.id,
        "image": movie.image,
        "title": movie.title,
        "year": movie.year,
        "description": movie.description,
        "directors": [
            {
                "id": directors.person_rel.id,
                "full_name": directors.person_rel.full_name,
                "image": directors.person_rel.image,
            }
        ],
        "cast": [
            {
                "id": c.person_rel.id,
                "full_name": c.person_rel.full_name,
                "image": c.person_rel.image,
            }
            for c in [c0, c1, c2]
        ],
    }
    return json.dumps(result)


def insert_movie_plus(sess, val):
    num = random.randrange(1_000_000)
    director = m.Person(
        first_name=f"{val}Alice",
        middle_name="",
        last_name=f"{val}Director",
        image=f"{val}image{num}.jpeg",
        bio="",
    )
    c0 = m.Person(
        first_name=f"{val}Billie",
        middle_name="",
        last_name=f"{val}Actor",
        image=f"{val}image{num+1}.jpeg",
        bio="",
    )
    c1 = m.Person(
        first_name=f"{val}Cameron",
        middle_name="",
        last_name=f"{val}Actor",
        image=f"{val}image{num+2}.jpeg",
        bio="",
    )
    movie = m.Movie(
        title=f"{val}{num}",
        image=f"{val}image{num}.jpeg",
        description=f"{val}description{num}",
        year=num,
    )

    sess.add_all([director, c0, c1, movie])
    sess.commit()

    sess.add_all(
        [
            m.Directors(person_rel=director, movie_rel=movie),
            m.Cast(person_rel=c0, movie_rel=movie),
            m.Cast(person_rel=c1, movie_rel=movie),
        ]
    )

    sess.commit()

    result = {
        "id": movie.id,
        "image": movie.image,
        "title": movie.title,
        "year": movie.year,
        "description": movie.description,
        "directors": [
            {
                "id": director.id,
                "full_name": director.full_name,
                "image": director.image,
            }
        ],
        "cast": [
            {
                "id": c.id,
                "full_name": c.full_name,
                "image": c.image,
            }
            for c in [c0, c1]
        ],
    }
    return json.dumps(result)


def setup(ctx, sess, queryname):
    if queryname == "update_movie":
        sess.execute(
            sa.update(m.Movie)
            .values(title=sa.func.split_part(m.Movie.title, "---", 1))
            .execution_options(synchronize_session=False)
        )
        sess.commit()
    elif queryname == "insert_user":
        sess.execute(
            sa.delete(m.User)
            .where(m.User.name.like(f"{INSERT_PREFIX}%"))
            .execution_options(synchronize_session=False)
        )
        sess.commit()
    elif queryname in {"insert_movie", "insert_movie_plus"}:

        sess.execute(
            sa.delete(m.Directors)
            .where(m.Directors.movie_rel)
            .where(m.Movie.image.like(f"{INSERT_PREFIX}%"))
            .execution_options(synchronize_session=False)
        )
        sess.execute(
            sa.delete(m.Cast)
            .where(m.Cast.movie_rel)
            .where(m.Movie.image.like(f"{INSERT_PREFIX}%"))
            .execution_options(synchronize_session=False)
        )
        sess.execute(
            sa.delete(m.Movie)
            .where(m.Movie.image.like(f"{INSERT_PREFIX}%"))
            .execution_options(synchronize_session=False)
        )
        sess.execute(
            sa.delete(m.Person)
            .where(m.Person.image.like(f"{INSERT_PREFIX}%"))
            .execution_options(synchronize_session=False)
        )
        sess.commit()


def cleanup(ctx, sess, queryname):
    if queryname in {
        "update_movie",
        "insert_user",
        "insert_movie",
        "insert_movie_plus",
    }:
        # The clean up is the same as setup for mutation benchmarks
        setup(ctx, sess, queryname)
