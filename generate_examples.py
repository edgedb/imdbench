import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate .eql and .json datasets for benchmarks.')
    parser.add_argument('people', type=int,
                        help='number of people')
    parser.add_argument('users', type=int,
                        help='number of users')
    parser.add_argument('reviews', type=int,
                        help='number of reviews')
    parser.add_argument('--new', dest='new', action='store_const',
                        const=True, default=False,
                        help='generate a new dataset')
    parser.add_argument('--importeql', dest='importeql', action='store_const',
                        const=True, default=False,
                        help='import the dataset directly to EdgeDB')

    args = parser.parse_args()

    import dataset
    from flask_edgedb.eqlgen import generate_eql
    from flask_edgedb.importer import import_data
    from django_bench.importer import generate_json
    dgen = dataset.DataGenerator(people=args.people, users=args.users,
                                 reviews=args.reviews, new=args.new)
    tail = f'{args.people}_{args.users}_{args.reviews}'

    if args.importeql:
        import_data(dgen)
    else:
        with open(f'setup_edgedb_{tail}.eql', 'wt') as f:
            f.write(generate_eql(dgen))

        with open(f'setup_django_{tail}.json', 'wt') as f:
            f.write(generate_json(dgen))

        with open(f'user_ids_{tail}.txt', 'wt') as f:
            f.write('\n'.join([str(nid) for nid in dgen.mdb['users']]))

        with open(f'person_ids_{tail}.txt', 'wt') as f:
            f.write('\n'.join([str(nid) for nid in dgen.mdb['people']]))

        with open(f'movie_ids_{tail}.txt', 'wt') as f:
            f.write('\n'.join([str(nid) for nid in dgen.mdb['movies']]))
