import flask
from flask_restful import Resource, Api, fields, marshal, reqparse
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload, selectinload
import os

from . import models
from .profiler import profiled
from .json import jsonify


app = flask.Flask('webapp')
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'postgresql://flask_bench:edgedbbenchmark@localhost/flask_bench'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['PROFILER'] = os.getenv('BENCH_DEBUG', '').lower() == 'true'
app.config['RAPID_JSONIFY'] = True
app.db = SQLAlchemy(app)
models.init(app.db)
app.manager = Manager(app)
app.api = Api(app)


@app.route('/')
def hello():
    return 'Flask + SQLAlchemy'


class BaseResource(Resource):
    def get(self, id=None):
        # no id indicates getting all objects
        query = self.Model.query

        if id is None:
            results = query.all()
        else:
            results = query.filter(self.Model.id == id).one()

        return marshal(results, self.mfields)


class User(BaseResource):
    Model = app.db.User
    mfields = {
        'id': fields.Integer,
        'name': fields.String,
        'image': fields.String,
    }


class Person(BaseResource):
    Model = app.db.Person
    mfields = {
        'id': fields.Integer,
        'image': fields.String,
        'first_name': fields.String,
        'middle_name': fields.String,
        'last_name': fields.String,
        'full_name': fields.String,
        'bio': fields.String,
    }


class Movie(BaseResource):
    Model = app.db.Movie
    mfields = {
        'id': fields.Integer,
        'image': fields.String,
        'title': fields.String,
        'year': fields.Integer,
        'description': fields.String,
        'directors': fields.List(fields.Nested({'id': fields.Integer})),
        'cast': fields.List(fields.Nested({'id': fields.Integer})),
    }


class Review(BaseResource):
    Model = app.db.Review
    mfields = {
        'id': fields.Integer,
        'body': fields.String,
        'rating': fields.Integer,
        'creation_time': fields.DateTime,
        'author_id': fields.Integer,
        'movie_id': fields.Integer,
    }


class TreeResource(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument('order', type=str, default=None)
    get_parser.add_argument('dir', type=str, default='asc')
    get_parser.add_argument('offset', type=int, default=0)
    get_parser.add_argument('limit', type=int, default=10)

    def dispatch_request(self, *args, **kwargs):
        resp = super().dispatch_request(*args, **kwargs)
        if flask.current_app.config.get('RAPID_JSONIFY'):
            # this makes it easy to add a custom JSON encoder without
            # having to worry about injecting SQL performance
            # statistics into the final result
            return jsonify(resp)
        else:
            # default Flask behavior
            return resp

    @profiled
    def get(self, id=None):
        args = self.get_parser.parse_args()
        args.order = args.order or self.default_order

        if id is not None:
            result = self.get_query().filter(self.Model.id == id).first()
            result = self.marshal(result)
        else:
            result = self.get_query().order_by(
                getattr(getattr(self.Model, args.order), args.dir)()
            ).offset(args.offset).limit(args.limit)

            result = [self.marshal(res) for res in result.all()]

        return result


class UserDetails(TreeResource):
    Model = app.db.User
    default_order = 'name'
    mfields = {
        'id': fields.Integer,
        'name': fields.String,
        'image': fields.String,
    }
    lr3_mfields = {
        'id': fields.Integer,
        'body': fields.String,
        'rating': fields.Integer,
        'movie': fields.Nested({
            'id': fields.Integer,
            'image': fields.String,
            'title': fields.String,
            'avg_rating': fields.Float,
        }),
    }

    def get_query(self):
        User = self.Model

        query = User.query

        return query

    def marshal(self, result):
        Review = app.db.Review
        # get only 3 latest_reviews joined with the corresponding
        # movies
        lr3 = result.latest_reviews.options(
            joinedload(Review.movie)
        ).limit(3).all()

        result = marshal(result, self.mfields)
        result['latest_reviews'] = marshal(lr3, self.lr3_mfields)

        return result


class PersonDetails(TreeResource):
    Model = app.db.Person
    default_order = 'last_name'
    mfields = {
        'id': fields.Integer,
        'full_name': fields.String,
        'image': fields.String,
        'bio': fields.String,
        'acted_in': fields.List(fields.Nested({
            'id': fields.Integer,
            'image': fields.String,
            'title': fields.String,
            'year': fields.Integer,
            'avg_rating': fields.Float,
        })),
        'directed': fields.List(fields.Nested({
            'id': fields.Integer,
            'image': fields.String,
            'title': fields.String,
            'year': fields.Integer,
            'avg_rating': fields.Float,
        })),
    }

    def get_query(self):
        Person = self.Model

        query = Person.query.options(
            joinedload(Person.acted_in),
            joinedload(Person.directed),
        )

        return query

    def marshal(self, result):
        result = marshal(result, self.mfields)

        # sorting can be done in Python
        if result['acted_in']:
            result['acted_in'].sort(key=lambda x: (x['year'], x['title']))
        if result['directed']:
            result['directed'].sort(key=lambda x: (x['year'], x['title']))

        return result


class MovieDetails(TreeResource):
    Model = app.db.Movie
    default_order = 'title'
    mfields = {
        'id': fields.Integer,
        'image': fields.String,
        'title': fields.String,
        'year': fields.Integer,
        'description': fields.String,
        'directors': fields.FormattedString('-'),   # placeholder
        'cast': fields.FormattedString('-'),        # placeholder
        'avg_rating': fields.Float,
        'reviews': fields.FormattedString('-'),     # placeholder
    }
    crew_mfields = {
        'id': fields.Integer,
        'full_name': fields.String,
        'image': fields.String,
    }
    reviews_mfields = {
        'id': fields.Integer,
        'body': fields.String,
        'rating': fields.Integer,
        'author': fields.Nested({
            'id': fields.Integer,
            'name': fields.String,
            'image': fields.String,
        }),
    }

    def get_query(self):
        Movie = self.Model
        Directors = app.db.Directors
        Cast = app.db.Cast
        Review = app.db.Review

        # NOTE: turns out that selectinload is better than joinedload
        # for directors, cast and reviews
        query = Movie.query.options(
            # get all the directors relationships in a subquery
            selectinload(Movie.directors_rel)
            .joinedload(Directors.person_rel, innerjoin=True),
            # get all the cast relationships in a subquery
            selectinload(Movie.cast_rel)
            .joinedload(Cast.person_rel, innerjoin=True),
            # get all the reviews in a subquery and join in authors
            selectinload(Movie.reviews)
            .joinedload(Review.author, innerjoin=True),
        )

        return query

    def marshal(self, result):
        # get the data to be massaged later
        directors_rel = result.directors_rel
        cast_rel = result.cast_rel
        reviews = result.reviews
        # marshal the main part
        result = marshal(result, self.mfields)

        # to implement NULLS LAST use a numeric value larger than any
        # list order we can get from the DB
        NULLS_LAST = 2 ^ 64

        def sort_key(rel):
            if rel.list_order is None:
                return (NULLS_LAST, rel.person_rel.last_name)
            else:
                return (rel.list_order, rel.person_rel.last_name)

        # directors
        directors = [rel.person_rel for rel in
                     sorted(directors_rel, key=sort_key)]
        result['directors'] = marshal(directors, self.crew_mfields)
        # cast
        cast = [rel.person_rel for rel in
                sorted(cast_rel, key=sort_key)]
        result['cast'] = marshal(cast, self.crew_mfields)
        # reviews
        reviews.sort(key=lambda x: x.creation_time, reverse=True)
        result['reviews'] = marshal(reviews, self.reviews_mfields)

        return result


app.api.add_resource(User, '/user/', '/user/<int:id>')
app.api.add_resource(Person, '/person/', '/person/<int:id>')
app.api.add_resource(Movie, '/movie/', '/movie/<int:id>')
app.api.add_resource(Review, '/review/', '/review/<int:id>')

app.api.add_resource(UserDetails,
                     '/user_details/<int:id>', '/pages/user_details/')
app.api.add_resource(PersonDetails,
                     '/person_details/<int:id>', '/pages/person_details/')
app.api.add_resource(MovieDetails,
                     '/movie_details/<int:id>', '/pages/movie_details/')
