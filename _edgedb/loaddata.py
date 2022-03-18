#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import argparse
import asyncio
import edgedb
import json
import progress.bar
import uvloop


async def import_data(data: dict):
    concurrency = 32
    client = edgedb.create_async_client(concurrency=concurrency)

    users = data['user']
    reviews = data['review']
    movies = data['movie']
    people = data['person']

    id2image_maps = {}
    for cat in ['user', 'person', 'movie']:
        id2image_maps[cat] = {r['id']: r['image'] for r in data[cat]}

    batch_size = 1000

    movies_data = [
        dict(
            _id=m['id'],
            title=m['title'],
            description=m['description'],
            year=m['year'],
            image=m['image'],
            directors=id2image(id2image_maps['person'], m['directors']),
            cast=id2image(id2image_maps['person'], m['cast']),
        ) for m in movies]
    ordered = [m for m in movies_data if m['_id'] % 10]
    unordered = [m for m in movies_data if not m['_id'] % 10]

    #################
    ## LOAD PEOPLE ##
    #################
    people_data = [
        dict(
            first_name=p['first_name'],
            middle_name=p['middle_name'],
            last_name=p['last_name'],
            image=p['image'],
            bio=p['bio']
        ) for p in people
    ]

    ppl_insert_query = r'''
        WITH people := <json>$people
        FOR person IN json_array_unpack(people) UNION (
        INSERT Person {
            first_name := <str>person['first_name'],
            middle_name := <str>person['middle_name'],
            last_name := <str>person['last_name'],
            image := <str>person['image'],
            bio := <str>person['bio'],
        });
    '''

    start = 0
    people_bar = progress.bar.Bar("Person", max=len(people))
    people_slice = people_data[start:start+batch_size]
    while len(people_slice):
        people_bar.goto(start)
        await client.query(ppl_insert_query, people=json.dumps(people_slice))
        start += batch_size
        people_slice = people_data[start:start+batch_size]
    people_bar.goto(people_bar.max)

    ################
    ## LOAD USERS ##
    ################
    users_data = [
        dict(
            name=u['name'],
            image=u['image'],
        ) for u in users
    ]

    users_insert_query = r'''
        WITH users := <json>$users
        FOR user IN json_array_unpack(users) UNION (
        INSERT User {
            name := <str>user['name'],
            image := <str>user['image'],
        });
    '''

    start = 0
    users_bar = progress.bar.Bar("User", max=len(users))
    users_slice = users_data[start:start+batch_size]
    while len(users_slice):
        users_bar.goto(start)
        await client.query(users_insert_query, users=json.dumps(users_slice))
        start += batch_size
        users_slice = users_data[start:start+batch_size]
    users_bar.goto(users_bar.max)

    #################
    ## LOAD MOVIES ##
    #################
    movies_data = [
        dict(
            _id=m['id'],
            title=m['title'],
            description=m['description'],
            year=m['year'],
            image=m['image'],
            directors=id2image(id2image_maps['person'], m['directors']),
            cast=id2image(id2image_maps['person'], m['cast']),
        ) for m in movies
    ]
    ordered = [m for m in movies_data if m['_id'] % 10]
    unordered = [m for m in movies_data if not m['_id'] % 10]

    start = 0
    movie_bar = progress.bar.Bar("Movie", max=len(movies))
    total_movies = 0
    ordered_slice = ordered[start:start+batch_size]
    while len(ordered_slice):
        movie_bar.goto(total_movies)

        await client.query(r'''
            WITH movies := <json>$movies
            FOR movie in json_array_unpack(movies) UNION (
            INSERT Movie {
                title := <str>movie['title'],
                description := <str>movie['description'],
                year := <int64>movie['year'],
                image := <str>movie['image'],

                directors := (
                    FOR X IN {
                        enumerate(array_unpack(
                            <array<str>>movie['directors']
                        ))
                    }
                    UNION (
                        SELECT Person {@list_order := X.0}
                        FILTER .image = X.1
                    )
                ),
                cast := (
                    FOR X IN {
                        enumerate(array_unpack(
                            <array<str>>movie['cast']
                        ))
                    }
                    UNION (
                        SELECT Person {@list_order := X.0}
                        FILTER .image = X.1
                    )
                )
            });
        ''', movies=json.dumps(ordered_slice))
        start += batch_size
        total_movies += batch_size
        ordered_slice = ordered[start:start+batch_size]

    start = 0
    batch_size = 100
    unordered_slice = unordered[start:start+batch_size]
    while len(unordered_slice):
        movie_bar.goto(total_movies)
        await client.query(r'''
            WITH movies := <json>$movies
            FOR movie in json_array_unpack(movies) UNION (
            INSERT Movie {
                title := <str>movie['title'],
                description := <str>movie['description'],
                year := <int64>movie['year'],
                image := <str>movie['image'],

                directors := (
                    FOR X IN {
                        enumerate(array_unpack(
                            <array<str>>movie['directors']
                        ))
                    }
                    UNION (
                        SELECT Person {@list_order := X.0}
                        FILTER .image = X.1
                    )
                ),
                cast := (
                    FOR X IN {
                        enumerate(array_unpack(
                            <array<str>>movie['cast']
                        ))
                    }
                    UNION (
                        SELECT Person
                        FILTER .image = X.1
                    )
                )
            });
        ''', movies=json.dumps(unordered_slice))
        start += batch_size
        total_movies += batch_size
        unordered_slice = unordered[start:start+batch_size]

    movie_bar.goto(movie_bar.max)

    ##################
    ## LOAD REVIEWS ##
    ##################

    reviews_data = [
        dict(
            body=r['body'],
            rating=r['rating'],
            uimage=id2image_maps['user'][r['author']],
            mimage=id2image_maps['movie'][r['movie']],
            creation_time=r['creation_time'][:-6],
        ) for r in reviews
    ]

    start = 0
    batch_size = 1000
    review_bar = progress.bar.Bar("Review", max=len(reviews))
    reviews_slice = reviews_data[start:start+batch_size]
    while len(reviews_slice):
        review_bar.goto(start)
        await client.query(r'''
        WITH reviews := <json>$reviews
        FOR review in json_array_unpack(reviews) UNION (
        INSERT Review {
            body := <str>review['body'],
            rating := <int64>review['rating'],
            author := (SELECT User FILTER .image = <str>review['uimage'] LIMIT 1),
            movie := (SELECT Movie FILTER .image = <str>review['mimage'] LIMIT 1),
            creation_time := <cal::local_datetime><str>review['creation_time'],
        });
      ''', reviews=json.dumps(reviews_slice))

        start += batch_size
        reviews_slice = reviews_data[start:start+batch_size]

    review_bar.goto(review_bar.max)


def id2image(idmap, ids):
    return [idmap[val] for val in ids]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Load EdgeDB dataset.')
    parser.add_argument('filename', type=str,
                        help='The JSON dataset file')
    args = parser.parse_args()

    with open(args.filename, 'rt') as f:
        records = json.load(f)

    uvloop.install()
    asyncio.run(import_data(records))
