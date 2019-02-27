from sqlalchemy import select, func
from sqlalchemy.orm import column_property


def init(db):
    class User(db.Model):
        id = db.Column(db.Integer(), primary_key=True)
        name = db.Column(db.String(), nullable=False)
        image = db.Column(db.String(), nullable=False)

        reviews = db.relationship(
            'Review', back_populates='author',
            cascade='all, delete, delete-orphan')
        latest_reviews = db.relationship(
            'Review', order_by=lambda: Review.creation_time.desc(),
            lazy='dynamic',
            bake_queries=True)

    db.User = User

    class Directors(db.Model):
        id = db.Column(db.Integer(), primary_key=True)
        list_order = db.Column(db.Integer(), nullable=True)

        person_id = db.Column(db.Integer, db.ForeignKey('person.id'),
                              nullable=False, index=True)
        person_rel = db.relationship('Person', back_populates='directed_rel')
        movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'),
                             nullable=False, index=True)
        movie_rel = db.relationship('Movie', back_populates='directors_rel')

    db.Directors = Directors

    class Cast(db.Model):
        id = db.Column(db.Integer(), primary_key=True)
        list_order = db.Column(db.Integer(), nullable=True)

        person_id = db.Column(db.Integer, db.ForeignKey('person.id'),
                              nullable=False, index=True)
        person_rel = db.relationship('Person', back_populates='acted_in_rel')

        movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'),
                             nullable=False, index=True)
        movie_rel = db.relationship('Movie', back_populates='cast_rel')

    db.Cast = Cast

    class Person(db.Model):
        id = db.Column(db.Integer(), primary_key=True)
        first_name = db.Column(db.String(), nullable=False)
        middle_name = db.Column(db.String(), nullable=False, server_default='')
        last_name = db.Column(db.String(), nullable=False)
        image = db.Column(db.String(), nullable=False)
        bio = db.Column(db.String(), nullable=False)

        # These are direct relationships between people and movies.
        # They are useful when the 'list_order' is irrelevant
        directed = db.relationship(
            'Movie',
            secondary=Directors.__table__,
            backref='directors',
        )
        acted_in = db.relationship(
            'Movie',
            secondary=Cast.__table__,
            backref='cast',
        )

        # The <blah>_rel relationships allow direct access to the
        # 'list_order' for purposes of modifying it or using it in some
        # sort of non-trivial sorting.
        directed_rel = db.relationship(
            Directors, back_populates='person_rel',
            cascade='all, delete, delete-orphan')
        acted_in_rel = db.relationship(
            Cast, back_populates='person_rel',
            cascade='all, delete, delete-orphan')

        @property
        def full_name(self):
            if self.middle_name:
                return f'{self.first_name} {self.middle_name} {self.last_name}'
            else:
                return f'{self.first_name} {self.last_name}'

    db.Person = Person

    class Review(db.Model):
        id = db.Column(db.Integer(), primary_key=True)
        body = db.Column(db.String(), nullable=False)
        rating = db.Column(db.Integer(), nullable=False)
        creation_time = db.Column(db.DateTime(), nullable=False)

        author_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                              nullable=False, index=True)
        author = db.relationship(User, back_populates='reviews')

        movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'),
                             nullable=False, index=True)
        movie = db.relationship('Movie', back_populates='reviews')

    db.Review = Review

    class Movie(db.Model):
        id = db.Column(db.Integer(), primary_key=True)
        image = db.Column(db.String(), nullable=False)
        title = db.Column(db.String(), nullable=False)
        year = db.Column(db.Integer(), nullable=False)
        description = db.Column(db.String(), nullable=False)

        reviews = db.relationship(
            Review, back_populates='movie',
            cascade='all, delete, delete-orphan')

        # The <blah>_rel relationships allow direct access to the
        # 'list_order' for purposes of modifying it or using it in some
        # sort of non-trivial sorting.
        directors_rel = db.relationship(
            Directors, back_populates='movie_rel',
            cascade='all, delete, delete-orphan')
        cast_rel = db.relationship(
            Cast, back_populates='movie_rel',
            cascade='all, delete, delete-orphan')

        # we want the avg_rating to be computed in SQL rather than in Python
        avg_rating = column_property(
            select(
                [func.avg(Review.rating)]
            ).where(
                Review.movie_id == id
            ).correlate_except(Review)
        )

    db.Movie = Movie
