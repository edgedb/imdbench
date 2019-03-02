import edgedb
from sanic import Sanic, response


app = Sanic('webapp')
app.config.EDGEDB_USER = 'edgedb'
app.config.EDGEDB_DATABASE = 'edgedb_bench'


NOT_FOUND = '{"detail": "Not found"}'


def resp(data):
    return response.text(
        data,
        headers={'Content-Type': 'application/json'},
        status=200
    )


@app.add_task
async def init(app):
    app.db = await edgedb.async_connect(
        user=app.config.EDGEDB_USER,
        database=app.config.EDGEDB_DATABASE,
    )


@app.route("/")
async def test(request):
    return response.text('Sanic + EdgeDB')


USER_DETAILS_EQL = r'''
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
    FILTER .id = <uuid>$id
'''


PERSON_DETAILS_EQL = r'''
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
    FILTER .id = <uuid>$id
'''


MOVIE_DETAILS_EQL = r'''
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
    FILTER .id = <uuid>$id
'''


@app.route('/user_details/<id:uuid>')
async def user_details(request, id):
    # simple user profile with 3 latest comments
    result = await app.db.fetch_json(USER_DETAILS_EQL, id=id)
    result = result[1:-1]

    if not result:
        result = NOT_FOUND

    return resp(result)


@app.route('/person_details/<id:uuid>')
async def person_details(request, id):
    # getting a person profile with movies that this person acted in
    # or directed
    result = await app.db.fetch_json(PERSON_DETAILS_EQL, id=id)
    result = result[1:-1]

    if not result:
        result = NOT_FOUND

    return resp(result)


@app.route('/movie_details/<id:uuid>')
async def movie_details(request, id):
    # getting movie profile with directors, cast, reviews, and average rating
    result = await app.db.fetch_json(MOVIE_DETAILS_EQL, id=id)
    result = result[1:-1]

    if not result:
        result = NOT_FOUND

    return resp(result)
