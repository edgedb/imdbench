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
import sys

import _shared
from bench import format_report_html


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("json_files")
    args = parser.parse_args()
    concurrencies = []
    benchmarks = {}
    for json_file in args.json_files:
        with open(json_file) as f:
            data = json.load(f)
        c = data["concurrency"]
        concurrencies.append(c)
        for k, v in data["benchmarks"].items():
            v[0]["implementation"] = f"concurrency:{c}"
            v[0]["concurrency"] = c
            benchmarks.setdefault(k, []).append(v[0])

    concurrencies.sort()
    for each in benchmarks.values():
        each.sort(key=lambda v: v["concurrency"])
    date = datetime.datetime.now().strftime("%c")
    report_data = {
        "date": date,
        "duration": data["duration"],
        "netlatency": data["netlatency"],
        "platform": data["platform"],
        "concurrency": ", ".join(map(str, concurrencies)),
        "benchmarks": benchmarks,
        "benchmarks_desc": _shared.BENCHMARKS,
        "implementations": [args.name],
    }
    format_report_html(report_data, sys.stdout, sort=False)


if __name__ == "__main__":
    main()
