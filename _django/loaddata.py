import argparse
import collections
import datetime
import json

from . import bootstrap  # NoQA
from . import models


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Load a specific fixture, old data will be purged.')
    parser.add_argument('filename', type=str,
                        help='The JSON dataset file')

    args = parser.parse_args()

    User = models.User
    Directors = models.Directors
    Cast = models.Cast
    Person = models.Person
    Movie = models.Movie
    Review = models.Review

    with open(args.filename, 'rt') as f:
        records = json.load(f)

    data = collections.defaultdict(list)
    for rec in records:
        rtype = rec['model'].split('.')[-1]
        datum = rec['fields']
        if 'pk' in rec:
            datum['id'] = rec['pk']
        # convert datetime
        if rtype == 'review':
            datum['creation_time'] = datetime.datetime.fromisoformat(
                datum['creation_time'])

        data[rtype].append(datum)

    batch_size = 1000

    # bulk create all the users
    print(f"Creating {len(data['user'])} users...")
    User.objects.bulk_create(
        [User(**datum) for datum in data['user']],
        batch_size=batch_size
    )

    # bulk create all the people
    print(f"Creating {len(data['person'])} people...")
    Person.objects.bulk_create(
        [Person(**datum) for datum in data['person']],
        batch_size=batch_size
    )

    # bulk create all the movies
    print(f"Creating {len(data['movie'])} movies...")
    Movie.objects.bulk_create(
        [Movie(**datum) for datum in data['movie']],
        batch_size=batch_size
    )

    # bulk create all the reviews
    print(f"Creating {len(data['review'])} reviews...")
    Review.objects.bulk_create(
        [Review(**datum) for datum in data['review']],
        batch_size=batch_size
    )

    # bulk create all the directors
    print(f"Creating {len(data['directors'])} directors...")
    Directors.objects.bulk_create(
        [Directors(**datum) for datum in data['directors']],
        batch_size=batch_size
    )

    # bulk create all the cast
    print(f"Creating {len(data['cast'])} cast...")
    Cast.objects.bulk_create(
        [Cast(**datum) for datum in data['cast']],
        batch_size=batch_size
    )
