#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import argparse

import dataset


def main():
    parser = argparse.ArgumentParser(
        description='Generate datasets for benchmarks.')
    parser.add_argument('people', type=int,
                        help='number of people')
    parser.add_argument('users', type=int,
                        help='number of users')
    parser.add_argument('reviews', type=int,
                        help='number of reviews')

    args = parser.parse_args()

    dgen = dataset.DataGenerator(args.people, args.users, args.reviews)
    dgen.generate_mdb()
    dgen.dump()


main()
