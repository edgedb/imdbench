import edgedb


def connect(ctx):
    return edgedb.connect(user='edgedb', database='edgedb_bench')


def close(ctx, conn):
    conn.close()


def load_ids(ctx, conn):
    d = conn.fetch_value('''
        WITH
            U := User {id, r := random()},
            M := Movie {id, r := random()},
            P := Person {id, r := random()}
        SELECT (
            users := array_agg((SELECT U ORDER BY U.r LIMIT <int64>$lim).id),
            movies := array_agg((SELECT M ORDER BY M.r LIMIT <int64>$lim).id),
            people := array_agg((SELECT P ORDER BY P.r LIMIT <int64>$lim).id),
        );
    ''', lim=ctx.number_of_ids)

    return dict(get_user=d.users, get_movie=d.movies, get_person=d.people)


def get_user(conn, id):
    return conn.fetch_json('''
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
    ''', id=id)


def get_movie(conn, id):
    return conn.fetch_json('''
        SELECT Movie {
            id,
            image,
            title,
            year,
            description,
            avg_rating,

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
    ''', id=id)


def get_person(conn, id):
    return conn.fetch_json('''
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
    ''', id=id)
