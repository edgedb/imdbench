import pymongo

import dataset


def main(data: dict):
    client = pymongo.MongoClient()
    client.drop_database('movies')

    db = client.movies

    ids_map = {}

    users = data['users']
    reviews = data['reviews']
    movies = data['movies']
    people = data['people']

    #############
    # people

    print(
        f'populating "people" collection with {len(people)} records... ',
        end='', flush=True)
    people_data = [
        dict(
            first_name=p.first_name,
            middle_name=p.middle_name,
            last_name=p.last_name,
            image=p.image,
            bio=p.bio
        )
        for p in people.values()
    ]
    result = db.people.insert_many(people_data)
    for p, id in zip(people.values(), result.inserted_ids):
        ids_map[p.image] = id
    print('done')

    #############
    # users
    print(
        f'populating "users" collection with {len(users)} records... ',
        end='', flush=True)
    users_data = [
        dict(
            name=u.name,
            image=u.image,
        )
        for u in users.values()
    ]
    result = db.users.insert_many(users_data)
    for u, id in zip(users.values(), result.inserted_ids):
        ids_map[u.image] = id
    print('done')

    #############
    # movies
    print(
        f'populating "movies" collection with {len(movies)} records... ',
        end='', flush=True)
    movies_data = [
        dict(
            title=m.title,
            description=m.description,
            year=m.year,
            image=m.image,
            directors=[ids_map[people[o].image] for o in m.directors],
            cast=[ids_map[people[o].image] for o in m.cast],
        )
        for m in movies.values()
    ]
    result = db.movies.insert_many(movies_data)
    for m, id in zip(movies.values(), result.inserted_ids):
        ids_map[m.image] = id
    print('done')

    #############
    # reviews
    print(
        f'populating "reviews" collection with {len(reviews)} records... ',
        end='', flush=True)
    reviews_data = [
        dict(
            body=r.body,
            rating=r.rating,
            author=ids_map[users[r.author_nid].image],
            movie=ids_map[movies[r.movie_nid].image],
            creation_time=r.creation_time,
        )
        for r in reviews.values()
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
    main(dataset.load())
