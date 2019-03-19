import json

import sqlalchemy as sa
import sqlalchemy.orm as orm

import _sqlalchemy.models as m


engine = sa.create_engine(
    'postgresql://sqlalch_bench:edgedbbenchmark@localhost/sqlalch_bench')

session_factory = orm.sessionmaker(bind=engine)


def connect(ctx):
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
    )


def get_user(sess, id):
    user = sess.query(m.User).filter_by(id=id).first()

    latest_reviews = user.latest_reviews.options(
        orm.joinedload(m.Review.movie)).limit(10).all()

    return json.dumps({
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


def get_movie(sess, id):
    # to implement NULLS LAST use a numeric value larger than any
    # list order we can get from the DB
    NULLS_LAST = 2 ^ 64

    def sort_key(rel):
        if rel.list_order is None:
            return (NULLS_LAST, rel.person_rel.last_name)
        else:
            return (rel.list_order, rel.person_rel.last_name)

    movie = sess.query(m.Movie) \
        .options(
            orm.selectinload(m.Movie.directors_rel)
            .joinedload(m.Directors.person_rel, innerjoin=True),

            orm.selectinload(m.Movie.cast_rel)
            .joinedload(m.Cast.person_rel, innerjoin=True),

            orm.selectinload(m.Movie.reviews)
            .joinedload(m.Review.author, innerjoin=True),
        ).filter_by(id=id).first()

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
    person = sess.query(m.Person).options(
        # using "selectinload" is apparently faster than
        # "joinedload" and "subqueryload" for this query.
        orm.selectinload(m.Person.acted_in),
        orm.selectinload(m.Person.directed),
    ).filter_by(id=id).first()

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
