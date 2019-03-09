import argparse
import dataset
import pathlib

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

    args = parser.parse_args()

    base_path = pathlib.Path(__file__).resolve().parent
    generate_new = True

    # check if the dataset pickle already exists
    pickle_path = dataset.DataGenerator.get_pickle_path(
        args.people, args.users, args.reviews)
    mdb = pathlib.Path('dataset') / pickle_path
    tail = mdb.name.split('_', 1)[1].split('.')[0]
    build_path = pickle_path.parent
    json_path = build_path / f'setup_dataset_{tail}.json'

    if mdb.exists():
        # check if the JSON dataset exists
        if json_path.exists():
            # we're done
            generate_new = False

    if generate_new:
        # generate a new dataset or read it from file
        dgen = dataset.DataGenerator(people=args.people, users=args.users,
                                     reviews=args.reviews, new=args.new)

        with open(json_path, 'wt') as f:
            f.write(json_generator.to_json(dgen))

        # extract the numerical IDs from the dataset pickle
        with open(build_path / f'user_ids_{tail}.txt', 'wt') as f:
            f.write('\n'.join([str(nid) for nid in dgen.mdb['users']]))

        with open(build_path / f'person_ids_{tail}.txt', 'wt') as f:
            f.write('\n'.join([str(nid) for nid in dgen.mdb['people']]))

        with open(build_path / f'movie_ids_{tail}.txt', 'wt') as f:
            f.write('\n'.join([str(nid) for nid in dgen.mdb['movies']]))

    # update the Makefile with the latest dataset pickle and parameters
    with open(base_path / 'Makefile.template', 'rt') as f:
        make = f.read()

    make = make.format(mdb=mdb.resolve(), json=json_path.resolve(), tail=tail,
                       people=args.people, users=args.users,
                       reviews=args.reviews)

    with open(base_path.parent / 'Makefile', 'wt') as f:
        f.write(make)
