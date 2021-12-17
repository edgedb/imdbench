#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import bson
import bson.json_util
import pymongo
from pymongo.collection import ReturnDocument
import random


INSERT_PREFIX = 'insert_test__'


def connect(ctx):
    client = pymongo.MongoClient(
        host=ctx.db_host,
        port=ctx.mongodb_port,

        # 1 is for "best speed" according to docs;
        # FWIW, setting this to 0 (disable) doesn't seem to change anything.
        zlibCompressionLevel=1,
    )
    db = client.movies
    return db


def close(ctx, db):
    db.client.close()


def load_ids(ctx, db):
    users = db.users.aggregate([{'$sample': {'size': ctx.number_of_ids}}])
    movies = db.movies.aggregate([{'$sample': {'size': ctx.number_of_ids}}])
    people = db.people.aggregate([{'$sample': {'size': ctx.number_of_ids}}])

    movies = list(movies)
    return dict(
        get_user=[d['_id'] for d in users],
        get_movie=[d['_id'] for d in movies],
        get_person=[d['_id'] for d in people],
        # re-use user IDs for update tests
        update_movie=[{
            'id': d['_id'],
            'title': f"{d['title']}---{str(d['_id'])[:8]}"
        } for d in movies],
        # generate as many insert stubs as "concurrency" to
        # accommodate concurrent inserts
        insert_user=[INSERT_PREFIX] * ctx.concurrency,
    )


def get_user(db, id):
    user = db.users.aggregate([
        {
            '$match': {
                '_id': id
            },
        },
        {
            '$lookup': {
                'from': 'reviews',
                'foreignField': 'author',
                'localField': '_id',
                'as': 'latest_reviews'
            }
        },
        {
            '$unwind': {
                'path': "$latest_reviews",
                'preserveNullAndEmptyArrays': True
            }
        },
        {
            '$sort': {"latest_reviews.creation_time": -1},
        },
        {
            '$limit': 10,
        },
        {
            '$lookup': {
                'from': 'reviews',
                'foreignField': 'movie',
                'localField': 'latest_reviews.movie',
                'as': 'latest_reviews.movie_reviews'
            }
        },
        {
            '$lookup': {
                'from': 'movies',
                'foreignField': '_id',
                'localField': 'latest_reviews.movie',
                'as': 'latest_reviews.movie'
            }
        },
        {
            '$project': {
                'name': 1,
                'image': 1,
                'latest_reviews': {
                    '_id': 1,
                    'body': 1,
                    'rating': 1,
                    'movie': {
                        '_id': 1,
                        'image': 1,
                        'title': 1,
                        'avg_rating': {
                            '$avg': '$latest_reviews.movie_reviews.rating'
                        }
                    },
                }
            }
        },
        {
            '$group': {
                '_id': "$_id",
                'name': {'$first': "$name"},
                'image': {'$first': "$image"},
                'latest_reviews': {'$push': "$latest_reviews"}
            }
        },
    ])

    user = list(user)
    result = bson.json_util.dumps(user[0])
    return result


def get_movie(db, id):
    movie = db.movies.aggregate([
        {
            '$match': {
                '_id': id
            }
        },
        {
            '$lookup': {
                'from': 'people',
                'localField': 'cast',
                'foreignField': '_id',
                'as': 'cast'
            }
        },
        {
            '$lookup': {
                'from': 'people',
                'localField': 'directors',
                'foreignField': '_id',
                'as': 'directors'
            }
        },
        {
            '$lookup': {
                'from': 'reviews',
                'foreignField': 'movie',
                'localField': '_id',
                'as': 'reviews'
            }
        },
        {
            '$unwind': {
                'path': "$reviews",
                'preserveNullAndEmptyArrays': True
            }
        },
        {
            '$lookup': {
                'from': 'users',
                'localField': 'reviews.author',
                'foreignField': '_id',
                'as': 'reviews.author'
            }
        },
        {
            '$sort': {"reviews.creation_time": -1},
        },
        {
            '$group': {
                '_id': "$_id",
                'title': {'$first': "$title"},
                'year': {'$first': "$year"},
                'image': {'$first': "$image"},
                'description': {'$first': "$description"},
                'cast': {'$first': "$cast"},
                'directors': {'$first': "$directors"},
                'reviews': {'$push': "$reviews"}
            }
        },
        {
            '$project': {
                'cast': {  # Calculating `full_name` adds around 5%
                           # overhead, but all other benchmarks do this,
                           # so it is fair to test how well mongodb
                           # performs with this kind of queries.
                    '$map': {
                        'input': '$cast',
                        'as': 'c',
                        'in': {
                            'name': {
                                "$concat": [
                                    "$$c.first_name",
                                    " ",
                                    {
                                        '$cond': {
                                            'if': {
                                                '$eq': ['$$c.middle_name', '']
                                            },
                                            'then': '',
                                            'else': {
                                                "$concat": [
                                                    "$$c.middle_name", ' '
                                                ]
                                            }
                                        }
                                    },
                                    "$$c.last_name"
                                ]
                            },
                            'image': '$$c.image',
                            '_id': '$$c._id',
                        }
                    }
                },
                'directors': {  # See the comment for "cast".
                    '$map': {
                        'input': '$directors',
                        'as': 'c',
                        'in': {
                            'name': {
                                "$concat": [
                                    "$$c.first_name",
                                    " ",
                                    {
                                        '$cond': {
                                            'if': {
                                                '$eq': ['$$c.middle_name', '']
                                            },
                                            'then': '',
                                            'else': {
                                                "$concat": [
                                                    "$$c.middle_name", ' '
                                                ]
                                            }
                                        }
                                    },
                                    "$$c.last_name"
                                ]
                            },
                            'image': '$$c.image',
                            '_id': '$$c._id',
                        }
                    }
                },
                'reviews': 1,
                'image': 1,
                'title': 1,
                'year': 1,
                'description': 1,
                'avg_rating': {'$avg': '$reviews.rating'}
            }
        }
    ])
    movie = list(movie)
    result = bson.json_util.dumps(movie[0])
    return result


def get_person(db, id):
    person = db.people.aggregate([
        {
            '$match': {
                '_id': id
            }
        },
        {
            '$lookup': {
                'from': 'movies',
                'foreignField': 'cast',
                'localField': '_id',
                'as': 'acted_in'
            }
        },
        {
            '$unwind': {
                'path': "$acted_in",
                'preserveNullAndEmptyArrays': True
            }
        },
        {
            '$sort': {"acted_in.year": 1, "acted_in.title": 1},
        },
        {
            '$lookup': {
                'from': 'reviews',
                'foreignField': 'movie',
                'localField': 'acted_in._id',
                'as': 'acted_in.reviews'
            }
        },
        {
            '$project': {
                'first_name': 1,
                'middle_name': 1,
                'last_name': 1,
                'image': 1,
                'bio': 1,
                'acted_in': {
                    '_id': 1,
                    'image': 1,
                    'title': 1,
                    'year': 1,
                    'avg_rating': {
                        '$avg': '$acted_in.reviews.rating'
                    },
                },
            }
        },
        {
            '$group': {
                '_id': "$_id",
                'first_name': {'$first': "$first_name"},
                'middle_name': {'$first': "$middle_name"},
                'last_name': {'$first': "$last_name"},
                'image': {'$first': "$image"},
                'bio': {'$first': "$bio"},
                'acted_in': {'$push': "$acted_in"},
            }
        },

        {
            '$lookup': {
                'from': 'movies',
                'foreignField': 'directors',
                'localField': '_id',
                'as': 'directed'
            }
        },
        {
            '$unwind': {
                'path': "$directed",
                'preserveNullAndEmptyArrays': True
            }
        },
        {
            '$sort': {"directed.year": 1},
        },
        {
            '$lookup': {
                'from': 'reviews',
                'foreignField': 'movie',
                'localField': 'directed._id',
                'as': 'directed.reviews'
            }
        },
        {
            '$project': {
                'first_name': 1,
                'middle_name': 1,
                'last_name': 1,
                'image': 1,
                'bio': 1,
                'acted_in': 1,
                'directed': {
                    '_id': 1,
                    'image': 1,
                    'title': 1,
                    'year': 1,
                    'avg_rating': {
                        '$avg': '$directed.reviews.rating'
                    },
                },
            }
        },
        {
            '$group': {
                '_id': "$_id",
                'first_name': {'$first': "$first_name"},
                'middle_name': {'$first': "$middle_name"},
                'last_name': {'$first': "$last_name"},
                'image': {'$first': "$image"},
                'bio': {'$first': "$bio"},
                'acted_in': {'$first': "$acted_in"},
                'directed': {'$push': "$directed"},
            }
        },
    ])

    person = list(person)
    return bson.json_util.dumps(person[0])


def update_movie(db, val):
    with db.client.start_session() as session:
        movie = db.movies.find_one_and_update(
            {
                '_id': val['id']
            },
            {
                '$set': {'title': val['title']},
            },
            projection={'_id': True, 'title': True},
            return_document=ReturnDocument.AFTER,
            session=session,
        )
        result = bson.json_util.dumps(movie)

    return result


def insert_user(db, val):
    with db.client.start_session() as session:
        num = random.randrange(1_000_000)
        user = db.users.insert_one(
            {
                'name': f'{val}{num}',
                'image': f'image_{val}{num}',
            },
            session=session,
        )
        result = bson.json_util.dumps(dict(
            _id=user.inserted_id,
            name=f'{val}{num}',
            image=f'image_{val}{num}',
        ))

    return result


def setup(ctx, db, queryname):
    if queryname == 'update_movie':
        with db.client.start_session() as session:
            movies = db.movies.find(
                {
                    'title': {'$regex': r'.+---.+'},
                },
                {
                    '_id': True,
                    'title': True,
                },
                session=session,
            )
            for mov in movies:
                db.movies.find_one_and_update(
                    {
                        '_id': mov['_id']
                    },
                    {
                        '$set': {'title': mov['title'].split('---')[0]},
                    },
                    session=session,
                )
    elif queryname == 'insert_user':
        with db.client.start_session() as session:
            db.users.delete_many(
                {
                    'name': {'$regex': f'{INSERT_PREFIX}.+'}
                },
                session=session,
            )


def cleanup(ctx, db, queryname):
    if queryname in {'update_movie', 'insert_user'}:
        # The clean up is the same as setup for mutation benchmarks
        setup(ctx, db, queryname)
