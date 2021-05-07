#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import argparse
import json
import pymongo


def main(data: dict):
    client = pymongo.MongoClient()
    client.drop_database('movies')

    db = client.movies

    ids_map = {'person': {}, 'user': {}, 'movie': {}}

    users = data['user']
    reviews = data['review']
    movies = data['movie']
    people = data['person']

    #############
    # people

    print(
        f'populating "people" collection with {len(people)} records... ',
        end='', flush=True)

    people_data = []
    for rec in people:
        datum = dict(rec)
        datum.pop('id')
        people_data.append(datum)

    result = db.people.insert_many(people_data)
    for p, id in zip(people, result.inserted_ids):
        ids_map['person'][p['id']] = id
    print('done')

    #############
    # users
    print(
        f'populating "users" collection with {len(users)} records... ',
        end='', flush=True)
    users_data = []
    for rec in users:
        datum = dict(rec)
        datum.pop('id')
        users_data.append(datum)

    result = db.users.insert_many(users_data)
    for u, id in zip(users, result.inserted_ids):
        ids_map['user'][u['id']] = id
    print('done')

    #############
    # movies
    print(
        f'populating "movies" collection with {len(movies)} records... ',
        end='', flush=True)
    movies_data = [
        dict(
            title=m['title'],
            description=m['description'],
            year=m['year'],
            image=m['image'],
            directors=[ids_map['person'][o] for o in m['directors']],
            cast=[ids_map['person'][o] for o in m['cast']],
        )
        for m in movies
    ]
    result = db.movies.insert_many(movies_data)
    for m, id in zip(movies, result.inserted_ids):
        ids_map['movie'][m['id']] = id
    print('done')

    #############
    # reviews
    print(
        f'populating "reviews" collection with {len(reviews)} records... ',
        end='', flush=True)
    reviews_data = [
        dict(
            body=r['body'],
            rating=r['rating'],
            author=ids_map['user'][r['author']],
            movie=ids_map['movie'][r['movie']],
            creation_time=r['creation_time'],
        )
        for r in reviews
    ]
    db.reviews.insert_many(reviews_data)
    print('done')

    #############
    # indexes
    indexes = [
        ('movies', 'directors'),
        ('movies', 'cast'),
        ('reviews', 'movie'),
        ('reviews', 'author'),
    ]

    for colname, fieldname in indexes:
        print(
            f'creating index on "{colname}" for field "{fieldname}"... ',
            end='', flush=True)
        db[colname].create_index([(fieldname, pymongo.ASCENDING)])
        print('done')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Load a specific fixture, old data will be purged.')
    parser.add_argument('filename', type=str,
                        help='The JSON dataset file')

    args = parser.parse_args()

    with open(args.filename, 'rt') as f:
        records = json.load(f)

    main(records)
