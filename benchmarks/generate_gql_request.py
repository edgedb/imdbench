import argparse
import pathlib
import re
import urllib.parse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate the URL encoded GraphQL query string.')
    parser.add_argument('query', type=str,
                        help='the GraphQL query file')

    args = parser.parse_args()

    gql = pathlib.Path(args.query).resolve()
    if not gql.exists():
        print(f'error: could not find {gql}')
        exit(1)

    with open(gql, 'rt') as f:
        query = f.read()

    query = re.sub(r'\s+', ' ', query).strip()
    query = urllib.parse.quote_plus(query)

    with open(gql.parent / f'{gql.name}.enc', 'wt') as f:
        f.write(query)
