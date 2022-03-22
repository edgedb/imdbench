#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import edgedb


INSERT_PREFIX = 'insert_test__'


def get_port(ctx):
    return ctx.edgedb_port


def get_queries(ctx):
    conn = connect(ctx)
    try:
        qargs = load_ids(ctx, conn)
    finally:
        close(ctx, conn)

    return {
        'get_user': {
            'query': GRAPHQL_GET_USER,
            'QArgs': qargs['get_user'],
        },
        'get_movie': {
            'query': GRAPHQL_GET_MOVIE,
            'QArgs': qargs['get_movie'],
        },
        'get_person': {
            'query': GRAPHQL_GET_PERSON,
            'QArgs': qargs['get_person'],
        },
        'update_movie': {
            'query': GRAPHQL_UPDATE_MOVIE,
            'QArgs': qargs['update_movie'],
        },
        'insert_user': {
            'query': GRAPHQL_INSERT_USER,
            'QArgs': qargs['insert_user'],
        },
        'insert_movie': {
            'query': GRAPHQL_INSERT_MOVIE,
            'QArgs': qargs['insert_movie'],
        },
        'insert_movie_plus': {
            'query': GRAPHQL_INSERT_MOVIE_PLUS,
            'QArgs': qargs['insert_movie_plus'],
        },
    }


def connect(ctx):
    return edgedb.create_client(max_concurrency=1)


def close(ctx, conn):
    conn.close()


def load_ids(ctx, conn):
    d = conn.query_single('''
        WITH
            U := User {id, r := random()},
            M := Movie {id, r := random()},
            P := Person {id, r := random()}
        SELECT (
            users := array_agg((SELECT U ORDER BY U.r LIMIT <int64>$lim).id),
            movies := array_agg((SELECT M ORDER BY M.r LIMIT <int64>$lim){
                id,
                title := '---' ++ (<str>.id)[:8],
            }),
            people := array_agg((SELECT P ORDER BY P.r LIMIT <int64>$lim).id),
        );
    ''', lim=ctx.number_of_ids)

    people = list(d.people)

    return dict(
        get_user=[[str(v)] for v in d.users],
        get_movie=[[str(v.id)] for v in d.movies],
        get_person=[[str(v)] for v in people],
        # re-use user IDs for update tests
        update_movie=[[str(v.id), v.title] for v in d.movies],
        # generate as many insert stubs as "concurrency" to
        # accommodate concurrent inserts
        insert_user=[[INSERT_PREFIX]] * ctx.concurrency,
        insert_movie=[
            [INSERT_PREFIX] + [str(v) for v in people[:4]]
        ] * ctx.concurrency,
        insert_movie_plus=[[INSERT_PREFIX]] * ctx.concurrency,
    )


def setup(ctx, conn, queryname):
    if queryname == 'update_movie':
        conn.execute('''
            update Movie
            filter contains(.title, '---')
            set {
                title := str_split(.title, '---')[0]
            };
        ''')
    elif queryname == 'insert_user':
        conn.query('''
            delete User
            filter .name LIKE <str>$prefix
        ''', prefix=f'{INSERT_PREFIX}%')
    elif queryname == 'insert_movie':
        conn.query('''
            delete Movie
            filter .image LIKE <str>$prefix
        ''', prefix=f'{INSERT_PREFIX}image%')
    elif queryname == 'insert_movie_plus':
        conn.query('''
            delete Movie
            filter .image LIKE <str>$prefix
        ''', prefix=f'{INSERT_PREFIX}image%')
        conn.query('''
            delete Person
            filter .image LIKE <str>$prefix
        ''', prefix=f'{INSERT_PREFIX}image%')


def cleanup(ctx, conn, queryname):
    if queryname in {'update_movie', 'insert_user', 'insert_movie',
                     'insert_movie_plus'}:
        # The clean up is the same as setup for mutation benchmarks
        setup(ctx, conn, queryname)


GRAPHQL_GET_USER = '''
    query user($id: ID!) {
        user: GraphQLUserDetails(filter: {id: {eq: $id}}) {
            id
            name
            image
            latest_reviews(
                order: {creation_time: {dir: DESC}}, first: 10
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
    query movie($id: ID!) {
        movie: GraphQLMovieDetails(filter: {id: {eq: $id}}) {
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
    query person($id: ID!) {
        person: GraphQLPersonDetails(filter: {id: {eq: $id}}) {
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


GRAPHQL_UPDATE_MOVIE = '''
    mutation update_movie($id: ID!, $title: String!) {
        movie: update_Movie(
            data: {
                title: {append: $title}
            },
            filter: {id: {eq: $id}}
        ) {
            id
            title
        }
    }
'''


GRAPHQL_INSERT_USER = '''
    mutation insert_user($name: String!, $image: String!) {
        user: insert_User(
            data: {
                name: $name,
                image: $image,
            }
        ) {
            id
            name
            image
        }
    }
'''


GRAPHQL_INSERT_MOVIE = '''
    mutation insert_movie(
        $title: String!,
        $image: String!,
        $description: String!,
        $year: Int64!,
        $did: ID!,
        $cid0: ID!,
        $cid1: ID!,
        $cid2: ID!,
    ) {
        movie: insert_Movie(
            data: {
                title: $title,
                image: $image,
                description: $description,
                year: $year,

                directors: [{
                    filter: {id: {eq: $did}}
                }],
                cast: [{
                    filter: {id: {eq: $cid0}},
                }, {
                    filter: {id: {eq: $cid1}},
                }, {
                    filter: {id: {eq: $cid2}},
                }]
            }
        ) {
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
        }
    }
'''


GRAPHQL_INSERT_MOVIE_PLUS = '''
    mutation insert_movie(
        $title: String!,
        $image: String!,
        $description: String!,
        $year: Int64!,
        $dfn: String!,
        $dln: String!,
        $dimg: String!,
        $cfn0: String!,
        $cln0: String!,
        $cimg0: String!,
        $cfn1: String!,
        $cln1: String!,
        $cimg1: String!,
    ) {
        movie: insert_Movie(
            data: {
                title: $title,
                image: $image,
                description: $description,
                year: $year,

                directors: [{
                    data: {
                        first_name: $dfn,
                        last_name: $dln,
                        image: $dimg,
                    }
                }],
                cast: [{
                    data: {
                        first_name: $cfn0,
                        last_name: $cln0,
                        image: $cimg0,
                    }
                }, {
                    data: {
                        first_name: $cfn1,
                        last_name: $cln1,
                        image: $cimg1,
                    }
                }]
            }
        ) {
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
        }
    }
'''
