import pymongo
import bson
import bson.json_util


def connect(ctx):
    client = pymongo.MongoClient()
    db = client.movies
    return db


def close(ctx, db):
    db.client.close()


def load_ids(ctx, db):
    users = db.users.aggregate([{'$sample': {'size': ctx.number_of_ids}}])
    movies = db.movies.aggregate([{'$sample': {'size': ctx.number_of_ids}}])
    people = db.people.aggregate([{'$sample': {'size': ctx.number_of_ids}}])

    return dict(
        get_user=[d['_id'] for d in users],
        get_movie=[d['_id'] for d in movies],
        get_person=[d['_id'] for d in people],
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
            '$limit': 3,
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
                'image': {'$first': "$image"},
                'cast': {'$first': "$cast"},
                'directors': {'$first': "$directors"},
                'reviews': {'$push': "$reviews"}
            }
        },
        {
            '$project': {
                'cast': {  # This adds around 5% overhead, but our other
                           # database benchmarks do this, so we might as well
                           # test how well mongo performs with this kinds of
                           # queries.
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
                'directors': {
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
                'reviews': 1,
                'image': 1,
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
