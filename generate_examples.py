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

    args = parser.parse_args()

    import dataset
    from edgedb.importer import generate_eql
    from django_bench.importer import generate_json
    dgen = dataset.DataGenerator(people=args.people, users=args.users,
                                 reviews=args.reviews, new=args.new)
    tail = f'{args.people}_{args.users}_{args.reviews}'

    with open(f'setup_edgedb_{tail}.eql', 'wt') as f:
        f.write(generate_eql(dgen))

    with open(f'setup_django_{tail}.json', 'wt') as f:
        f.write(generate_json(dgen))
