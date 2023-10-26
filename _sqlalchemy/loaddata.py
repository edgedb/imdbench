#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import argparse
import collections
import datetime
import json
import os
import progress.bar

import sqlalchemy as sa
import sqlalchemy.orm as orm

import _sqlalchemy.models as m


def bar(label, total):
    return progress.bar.Bar(label[:32].ljust(32), max=total)


def bulk_insert(db, label, data, into):
    label = f"Creating {len(data)} {label}"
    pbar = bar(label, len(data))

    while data:
        chunk = data[:1000]
        data = data[1000:]
        db.execute(sa.insert(into), chunk)
        db.commit()
        pbar.next(len(chunk))
    pbar.finish()


def reset_sequence(db, tablename):
    tab = sa.table(tablename, sa.column("id"))

    db.execute(
        sa.select(
            sa.func.setval(
                f"{tablename}_id_seq",
                sa.select(tab.c.id)
                .order_by(tab.c.id.desc())
                .limit(1)
                .scalar_subquery(),
            )
        )
    )


def load_data(filename, engine):
    session_factory = orm.sessionmaker(bind=engine)
    Session = orm.scoped_session(session_factory)

    with Session() as db:

        # first clear all the existing data
        print(f"purging existing data...")

        db.execute(sa.delete(m.Directors))
        db.execute(sa.delete(m.Cast))
        db.execute(sa.delete(m.Review))
        db.execute(sa.delete(m.Movie))
        db.execute(sa.delete(m.Person))
        db.execute(sa.delete(m.User))
        db.commit()

    # read the JSON data
    print("loading JSON... ", end="", flush=True)
    with open(filename, "rt") as f:
        records = json.load(f)
    data = collections.defaultdict(list)
    for rec in records:
        rtype = rec["model"].split(".")[-1]
        datum = rec["fields"]
        if "pk" in rec:
            datum["id"] = rec["pk"]
        # convert datetime
        if rtype == "review":
            datum["creation_time"] = datetime.datetime.fromisoformat(
                datum["creation_time"]
            )

        data[rtype].append(datum)
    print("done")

    with Session() as db:

        # bulk create all the users
        bulk_insert(db, "users", data["user"], m.User)

        # bulk create all the people
        bulk_insert(db, "people", data["person"], m.Person)

        # bulk create all the movies
        bulk_insert(db, "movies", data["movie"], m.Movie)

        # bulk create all the reviews
        bulk_insert(db, "reviews", data["review"], m.Review)

        # bulk create all the directors
        bulk_insert(db, "directors", data["directors"], m.Directors)

        # bulk create all the cast
        bulk_insert(db, "cast", data["cast"], m.Cast)

        # reconcile the autoincrementing indexes with the actual indexes
        reset_sequence(db, sa.sql.quoted_name("cast", True))
        reset_sequence(db, "directors")
        reset_sequence(db, "movie")
        reset_sequence(db, "person")
        reset_sequence(db, "user")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load a specific fixture, old data will be purged."
    )
    parser.add_argument("filename", type=str, help="The JSON dataset file")

    args = parser.parse_args()

    engine = sa.create_engine(
        os.environ.get(
            "SQLA_DSN",
            "postgresql+asyncpg://sqlalch_bench:edgedbbenchmark@"
            "localhost:15432/sqlalch_bench?async_fallback=true",
        )
    )

    load_data(args.filename, engine)
