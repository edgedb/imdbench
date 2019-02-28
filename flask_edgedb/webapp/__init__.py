import edgedb
import flask
from flask_script import Manager
import os


app = flask.Flask('webapp')
app.config['EDGEDB_USER'] = 'edgedb'
app.config['EDGEDB_DATABASE'] = 'edgedb_bench'
app.db = edgedb.connect(
    user=app.config.get('EDGEDB_USER'),
    database=app.config.get('EDGEDB_DATABASE'),
)
app.manager = Manager(app)

NOT_FOUND = '{"detail": "Not found"}'


@app.route('/')
def hello():
    return 'Flask + EdgeDB'


@app.route('/user_details/<uuid:id>')
def user_details(id):
    # simple user profile with 3 latest comments
    result = app.db.fetch_json(r'''
        SELECT User {
            id,
            name,
            image,
            latest_reviews := (
                WITH UserReviews := User.<author
                SELECT UserReviews {
                    id,
                    body,
                    rating,
                    movie: {
                        id,
                        image,
                        title,
                        avg_rating
                    }
                }
                ORDER BY .creation_time DESC
                LIMIT 3
            )
        }
        FILTER .id = <uuid>$id;
    ''', id=id)
    result = result[1:-1]

    if not result:
        result = NOT_FOUND

    return flask.Response(result, content_type='application/json')


@app.route('/person_details/<uuid:id>')
def person_details(id):
    # getting a person profile with movies that this person acted in or directed
    result = app.db.fetch_json(r'''
        SELECT Person {
            id,
            full_name,
            image,
            bio,

            # computables
            acted_in := (
                WITH M := Person.<cast
                SELECT M {
                    id,
                    image,
                    title,
                    year,
                    avg_rating
                }
                ORDER BY .year ASC THEN .title ASC
            ),
            directed := (
                WITH M := Person.<directors
                SELECT M {
                    id,
                    image,
                    title,
                    year,
                    avg_rating
                }
                ORDER BY .year ASC THEN .title ASC
            ),
        }
        FILTER .id = <uuid>$id;
    ''', id=id)
    result = result[1:-1]

    if not result:
        result = NOT_FOUND

    return flask.Response(result, content_type='application/json')


@app.route('/movie_details/<uuid:id>')
def movie_details(id):
    # getting movie profile with directors, cast, reviews, and average rating
    result = app.db.fetch_json(r'''
        SELECT Movie {
            id,
            image,
            title,
            year,
            description,
            directors: {
                id,
                full_name,
                image,
            }
            ORDER BY Movie.directors@list_order EMPTY LAST
                THEN Movie.directors.last_name,
            cast: {
                id,
                full_name,
                image,
            }
            ORDER BY Movie.cast@list_order EMPTY LAST
                THEN Movie.cast.last_name,
            avg_rating,

            # computables
            reviews := (
                SELECT Movie.<movie {
                    id,
                    body,
                    rating,
                    author: {
                        id,
                        name,
                        image,
                    }
                }
                ORDER BY .creation_time DESC
            ),
        }
        FILTER .id = <uuid>$id;
    ''', id=id)
    result = result[1:-1]

    if not result:
        result = NOT_FOUND

    return flask.Response(result, content_type='application/json')
