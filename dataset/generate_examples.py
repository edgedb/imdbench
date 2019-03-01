import asyncio
import argparse
import edgedb

import edgedb_importer
import json_generator


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate datasets for benchmarks.')
    parser.add_argument('people', type=int,
                        help='number of people')
    parser.add_argument('users', type=int,
                        help='number of users')
    parser.add_argument('reviews', type=int,
                        help='number of reviews')
    parser.add_argument('--new', dest='new', action='store_const',
                        const=True, default=False,
                        help='generate a new dataset')
    parser.add_argument('--json', dest='makejson', action='store_const',
                        const=True, default=False,
                        help='generate the JSON datasets and corresponding '
                             'nid files')
    parser.add_argument('--importeql', dest='importeql', action='store_const',
                        const=True, default=False,
                        help='import the dataset directly to EdgeDB')
    parser.add_argument('--edgedb_ids', dest='edgedb_ids',
                        action='store_const', const=True, default=False,
                        help='generate id files from EdgeDB data')

    args = parser.parse_args()

    import dataset
    dgen = dataset.DataGenerator(people=args.people, users=args.users,
                                 reviews=args.reviews, new=args.new)
    tail = f'{args.people}_{args.users}_{args.reviews}'

    if args.importeql:
        asyncio.run(edgedb_importer.import_data(dgen))

    # importing a new dataset means that the IDs need to be extracted again
    if args.importeql or args.edgedb_ids:
        con = edgedb.connect(user='edgedb', database='edgedb_bench')

        with open(f'edgedb_user_ids_{tail}.txt', 'wt') as f:
            for res in con.fetch('SELECT User.id'):
                f.write(f'{res}\n')

        with open(f'edgedb_person_ids_{tail}.txt', 'wt') as f:
            for res in con.fetch('SELECT Person.id'):
                f.write(f'{res}\n')

        with open(f'edgedb_movie_ids_{tail}.txt', 'wt') as f:
            for res in con.fetch('SELECT Movie.id'):
                f.write(f'{res}\n')

    if args.makejson:
        with open(f'setup_dataset_{tail}.json', 'wt') as f:
            f.write(json_generator.to_json(dgen))

        with open(f'user_ids_{tail}.txt', 'wt') as f:
            f.write('\n'.join([str(nid) for nid in dgen.mdb['users']]))

        with open(f'person_ids_{tail}.txt', 'wt') as f:
            f.write('\n'.join([str(nid) for nid in dgen.mdb['people']]))

        with open(f'movie_ids_{tail}.txt', 'wt') as f:
            f.write('\n'.join([str(nid) for nid in dgen.mdb['movies']]))
