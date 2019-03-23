#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import edgedb


def get_port(ctx):
    return 8888


def get_queries(ctx):
    conn = connect(ctx)
    try:
        ids = load_ids(ctx, conn)
    finally:
        close(ctx, conn)

    return {
        'get_user': {
            'query': GRAPHQL_GET_USER,
            'ids': ids['get_user'],
        },
        'get_movie': {
            'query': GRAPHQL_GET_MOVIE,
            'ids': ids['get_movie'],
        },
        'get_person': {
            'query': GRAPHQL_GET_PERSON,
            'ids': ids['get_person'],
        },
    }


def connect(ctx):
    return edgedb.connect(
        user=ctx.edgedb_user, database='edgedb_bench',
        host=ctx.db_host, port=ctx.edgedb_port)


def close(ctx, conn):
    conn.close()


def load_ids(ctx, conn):
    d = conn.fetchone('''
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

    return dict(
        get_user=[str(v) for v in d.users],
        get_movie=[str(v) for v in d.movies],
        get_person=[str(v) for v in d.people],
    )


GRAPHQL_GET_USER = '''
    query user($id: ID) {
        GraphQLUserDetails(filter: {id: {eq: $id}}) {
        id
        name
        image
        latest_reviews(
            order: {creation_time: {dir: DESC}}, first: 3
        ) {
            id
            body
            rating
            movie {
            id
            image
            title
            avg_rating
            }
        }
        }
    }
'''

GRAPHQL_GET_MOVIE = '''
    query movie($id: ID) {
        GraphQLMovieDetails(filter: {id: {eq: $id}}) {
        id
        image
        title
        year
        description
        directors {
            id
            full_name
            image
        }
        cast {
            id
            full_name
            image
        }
        avg_rating
        reviews(order: {creation_time: {dir: DESC}}) {
            id
            body
            rating
            author {
            id
            name
            image
            }
        }
        }
    }
'''


GRAPHQL_GET_PERSON = '''
    query person($id: ID) {
        GraphQLPersonDetails(filter: {id: {eq: $id}}) {
        id
        full_name
        image
        bio
        acted_in(order: {year: {dir: ASC}, title: {dir: ASC}}) {
            id
            image
            title
            year
            avg_rating
        }
        directed(order: {year: {dir: ASC}, title: {dir: ASC}}) {
            id
            image
            title
            year
            avg_rating
        }
        }
    }
'''
