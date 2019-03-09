import pathlib


if __name__ == '__main__':
    base_path = pathlib.Path(__file__).resolve().parent

    with open(base_path / 'dataset' / 'Makefile.template', 'rt') as f:
        make = f.read()

    # just populate the Makefile with defaults
    mdb = base_path / 'dataset' / 'build' / 'mdb_100000_100000_500000.pickle'
    make = make.format(mdb=mdb, json='', tail='',
                       people=100_000, users=100_000, reviews=500_000)

    with open(base_path / 'Makefile', 'wt') as f:
        f.write(make)
