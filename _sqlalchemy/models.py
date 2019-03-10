import sqlalchemy as sa
import sqlalchemy.orm as orm

from sqlalchemy import select, func

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = sa.Column(sa.Integer(), primary_key=True)
    name = sa.Column(sa.String(), nullable=False)
    image = sa.Column(sa.String(), nullable=False)

    reviews = orm.relationship(
        'Review', back_populates='author',
        cascade='all, delete, delete-orphan')
    latest_reviews = orm.relationship(
        'Review', order_by=lambda: Review.creation_time.desc(),
        lazy='dynamic', bake_queries=True)


class Directors(Base):
    __tablename__ = 'directors'

    id = sa.Column(sa.Integer(), primary_key=True)
    list_order = sa.Column(sa.Integer(), nullable=True)

    person_id = sa.Column(sa.Integer, sa.ForeignKey('person.id'),
                          nullable=False, index=True)
    person_rel = orm.relationship('Person', back_populates='directed_rel')
    movie_id = sa.Column(sa.Integer, sa.ForeignKey('movie.id'),
                         nullable=False, index=True)
    movie_rel = orm.relationship('Movie', back_populates='directors_rel')


class Cast(Base):
    __tablename__ = 'cast'

    id = sa.Column(sa.Integer(), primary_key=True)
    list_order = sa.Column(sa.Integer(), nullable=True)

    person_id = sa.Column(sa.Integer, sa.ForeignKey('person.id'),
                          nullable=False, index=True)
    person_rel = orm.relationship('Person', back_populates='acted_in_rel')

    movie_id = sa.Column(sa.Integer, sa.ForeignKey('movie.id'),
                         nullable=False, index=True)
    movie_rel = orm.relationship('Movie', back_populates='cast_rel')


class Person(Base):
    __tablename__ = 'person'

    id = sa.Column(sa.Integer(), primary_key=True)
    first_name = sa.Column(sa.String(), nullable=False)
    middle_name = sa.Column(sa.String(), nullable=False, server_default='')
    last_name = sa.Column(sa.String(), nullable=False)
    image = sa.Column(sa.String(), nullable=False)
    bio = sa.Column(sa.String(), nullable=False)

    # These are direct relationships between people and movies.
    # They are useful when the 'list_order' is irrelevant
    directed = orm.relationship(
        'Movie',
        secondary=Directors.__table__,
        backref='directors',
    )
    acted_in = orm.relationship(
        'Movie',
        secondary=Cast.__table__,
        backref='cast',
    )

    # The <blah>_rel relationships allow direct access to the
    # 'list_order' for purposes of modifying it or using it in some
    # sort of non-trivial sorting.
    directed_rel = orm.relationship(
        Directors, back_populates='person_rel',
        cascade='all, delete, delete-orphan')
    acted_in_rel = orm.relationship(
        Cast, back_populates='person_rel',
        cascade='all, delete, delete-orphan')

    @property
    def full_name(self):
        if self.middle_name:
            return f'{self.first_name} {self.middle_name} {self.last_name}'
        else:
            return f'{self.first_name} {self.last_name}'


class Review(Base):
    __tablename__ = 'review'

    id = sa.Column(sa.Integer(), primary_key=True)
    body = sa.Column(sa.String(), nullable=False)
    rating = sa.Column(sa.Integer(), nullable=False)
    creation_time = sa.Column(sa.DateTime(), nullable=False)

    author_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'),
                          nullable=False, index=True)
    author = orm.relationship(User, back_populates='reviews')

    movie_id = sa.Column(sa.Integer, sa.ForeignKey('movie.id'),
                         nullable=False, index=True)
    movie = orm.relationship('Movie', back_populates='reviews')


class Movie(Base):
    __tablename__ = 'movie'

    id = sa.Column(sa.Integer(), primary_key=True)
    image = sa.Column(sa.String(), nullable=False)
    title = sa.Column(sa.String(), nullable=False)
    year = sa.Column(sa.Integer(), nullable=False)
    description = sa.Column(sa.String(), nullable=False)

    reviews = orm.relationship(
        Review, back_populates='movie',
        cascade='all, delete, delete-orphan')

    # The <blah>_rel relationships allow direct access to the
    # 'list_order' for purposes of modifying it or using it in some
    # sort of non-trivial sorting.
    directors_rel = orm.relationship(
        Directors, back_populates='movie_rel',
        cascade='all, delete, delete-orphan')
    cast_rel = orm.relationship(
        Cast, back_populates='movie_rel',
        cascade='all, delete, delete-orphan')

    # we want the avg_rating to be computed in SQL rather than in Python
    avg_rating = orm.column_property(
        select(
            [func.avg(Review.rating)]
        ).where(
            Review.movie_id == id
        ).correlate_except(Review)
    )
