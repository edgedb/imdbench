#!/usr/bin/env python3
#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##

import argparse
import datetime
import json
import pathlib
import sys

import _shared
from bench import format_report_html


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sort-by-concurrency", action="store_true", default=False)
    parser.add_argument("json_files", nargs='*')
    args = parser.parse_args()
    concurrencies = []
    benchmarks = {}
    implementations = []
    for json_file in args.json_files:
        with open(json_file) as f:
            data = json.load(f)
        c = data["concurrency"]
        concurrencies.append(c)
        for k, v in data["benchmarks"].items():
            vv = v[0].copy()
            if args.sort_by_concurrency:
                vv["implementation"] = str(c)
            else:
                vv["implementation"] = pathlib.Path(json_file).stem

            vv["concurrency"] = c
            benchmarks.setdefault(k, []).append(vv)
        implementations.append(v[0]["implementation"])

    if args.sort_by_concurrency:
        concurrencies.sort()
        for each in benchmarks.values():
            each.sort(key=lambda x: x["concurrency"])
        implementations = [v[0]["implementation"]]
    else:
        implementations = [
            d['implementation'] for d in next(iter(benchmarks.values()))
        ]

    date = datetime.datetime.now().strftime("%c")
    report_data = {
        "date": date,
        "duration": data["duration"],
        "netlatency": data["netlatency"],
        "platform": data["platform"],
        "concurrency": ", ".join(map(str, concurrencies)),
        "benchmarks": benchmarks,
        "benchmarks_desc": _shared.BENCHMARKS,
        "implementations": implementations,
    }
    format_report_html(report_data, sys.stdout, sort=False)


if __name__ == "__main__":
    main()
