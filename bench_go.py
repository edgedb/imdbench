#!/usr/bin/env python3

#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import json
import pathlib
import subprocess
import typing

import numpy as np

import _shared


class Result(typing.NamedTuple):

    benchmark: str
    queryname: str
    nqueries: int
    duration: int
    min_latency: int
    avg_latency: int
    max_latency: int
    latency_stats: typing.List[int]
    samples: typing.List[str]


def print_result(ctx, result: Result):
    print(f'== {result.benchmark} : {result.queryname} ==')
    print(f'queries:\t{result.nqueries}')
    print(f'qps:\t\t{result.nqueries // ctx.duration} q/s')
    print(f'min latency:\t{result.min_latency / 100:.2f}ms')
    print(f'avg latency:\t{result.avg_latency / 100:.2f}ms')
    print(f'max latency:\t{result.max_latency / 100:.2f}ms')
    print()


def run_query(ctx, benchmark, queryname, querydata, port):
    dirn = pathlib.Path(_shared.IMPLEMENTATIONS[benchmark].module.__file__)
    exe = dirn.parent.parent / 'gobench'

    # Hasura needs a special GraphQL API path, otherwise it should be ignored

    if 'hasura' in benchmark:
        path = '/v1/graphql'
    elif 'edgedb_go_graphql' == benchmark:
        path = "/db/edgedb/graphql"
    elif 'edgedb_go_http' == benchmark:
        path = "/db/edgedb/edgeql"
    else:
        path = "/"

    int_ids = 'edgedb' not in benchmark

    cmd = [exe, '--concurrency', ctx.concurrency, '--duration', ctx.duration,
           '--timeout', ctx.timeout, '--warmup-time', ctx.warmup_time,
           '--output-format', 'json', '--host', ctx.db_host,
           '--port', port, '--path', path, '--ids-are-ints', int_ids,
           '--nsamples', '10', '--benchmark', benchmark,
           '--queryname', queryname, '--', '-']

    cmd = [str(c) for c in cmd]

    try:
        proc = subprocess.run(
            cmd, input=json.dumps(querydata), text=True,
            capture_output=True, check=True,
        )
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        raise

    data = json.loads(proc.stdout)

    avg_latency = np.average(
        np.arange(len(data['latency_stats'])),
        weights=data['latency_stats'])

    return Result(
        benchmark=benchmark,
        queryname=queryname,
        nqueries=data['nqueries'],
        duration=data['duration'],
        min_latency=data['min_latency'],
        avg_latency=avg_latency,
        max_latency=data['max_latency'],
        latency_stats=data['latency_stats'],
        samples=data['samples'],
    )


def run_bench(ctx, benchmark, queries_mod):
    results = []
    queries = queries_mod.get_queries(ctx)
    port = queries_mod.get_port(ctx)

    for queryname in ctx.queries:
        querydata = queries[queryname]

        # Potentially setup the benchmark state
        conn = queries_mod.connect(ctx)
        queries_mod.setup(ctx, conn, queryname)
        queries_mod.close(ctx, conn)

        res = run_query(ctx, benchmark, queryname, querydata, port)
        results.append(res)
        print_result(ctx, res)

        # Potentially clean up after the benchmarks
        conn = queries_mod.connect(ctx)
        queries_mod.cleanup(ctx, conn, queryname)
        queries_mod.close(ctx, conn)

    return results


def main():
    ctx, _ = _shared.parse_args(
        prog_desc='EdgeDB Databases Benchmark (Go drivers)',
        out_to_json=True)

    print('============ Go ============')
    print(f'concurrency:\t{ctx.concurrency}')
    print(f'warmup time:\t{ctx.warmup_time} seconds')
    print(f'duration:\t{ctx.duration} seconds')
    print(f'queries:\t{", ".join(q for q in ctx.queries)}')
    print(f'benchmarks:\t{", ".join(b for b in ctx.benchmarks)}')
    print()

    data = []

    for benchmark in ctx.benchmarks:
        bench_desc = _shared.IMPLEMENTATIONS[benchmark]

        if bench_desc.language != 'go':
            continue

        queries_mod = _shared.IMPLEMENTATIONS[benchmark].module
        res = run_bench(ctx, benchmark, queries_mod)
        data.append(res)

    if ctx.json:
        json_data = []

        for results in data:
            json_results = []

            for r in results:
                json_results.append({
                    'queryname': r.queryname,
                    'nqueries': r.nqueries,
                    'min_latency': r.min_latency,
                    'max_latency': r.max_latency,
                    'latency_stats': [int(i) for i in r.latency_stats],
                    'samples': r.samples,
                })
            json_data.append({
                'benchmark': results[0].benchmark,
                'duration': results[0].duration,
                'queries': json_results,
            })

        data = json.dumps({
            'language': 'go',
            'concurrency': ctx.concurrency,
            'warmup_time': ctx.warmup_time,
            'duration': ctx.duration,
            'data': json_data,
        })
        with open(ctx.json, 'wt') as f:
            f.write(data)


if __name__ == '__main__':
    main()
