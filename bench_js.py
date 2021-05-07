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

import _shared


class Result(typing.NamedTuple):

    benchmark: str
    queryname: str
    nqueries: int
    duration: int
    min_latency: int
    max_latency: int
    latency_stats: typing.List[int]
    samples: typing.List[str]


def print_result(ctx, result: Result):
    print(f'== {result.benchmark} : {result.queryname} ==')
    print(f'queries:\t{result.nqueries}')
    print(f'qps:\t\t{result.nqueries // ctx.duration} q/s')
    print(f'min latency:\t{result.min_latency / 100:.2f}ms')
    print(f'max latency:\t{result.max_latency / 100:.2f}ms')
    print()


def run_query(ctx, benchmark, queryname):
    dirn = pathlib.Path(__file__).resolve().parent
    exe = dirn / 'jsbench.js'

    if benchmark.startswith('edgedb'):
        port = ctx.edgedb_port
    else:
        port = ctx.pg_port

    # If we're running Prisma benchmark we need to update the `.env`
    # file with the pool size and timeout info.
    if benchmark == 'postgres_prisma_js':
        with open('_prisma/.env', 'wt') as f:
            f.write(
                f'DATABASE_URL="postgresql://postgres_bench:edgedbbenchmark@'
                f'localhost:5432/postgres_bench'
                f'?schema=public'
                f'&connection_limit={ctx.concurrency}'
                f'&pool_timeout={ctx.timeout}"')

    cmd = [exe, '--concurrency', ctx.concurrency, '--duration', ctx.duration,
           '--timeout', ctx.timeout, '--warmup-time', ctx.warmup_time,
           '--output-format', 'json', '--host', ctx.db_host,
           '--port', port, '--nsamples', 10, '--number-of-ids', ctx.number_of_ids,
           '--query', queryname, benchmark]

    cmd = [str(c) for c in cmd]

    try:
        proc = subprocess.run(
            cmd, text=True, capture_output=True, check=True,
        )
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        raise

    data = json.loads(proc.stdout)

    return Result(
        benchmark=benchmark,
        queryname=queryname,
        nqueries=data['nqueries'],
        duration=data['duration'],
        min_latency=data['min_latency'],
        max_latency=data['max_latency'],
        latency_stats=data['latency_stats'],
        samples=data['samples'],
    )


def run_bench(ctx, benchmark):
    results = []

    for queryname in ctx.queries:
        res = run_query(ctx, benchmark, queryname)
        results.append(res)
        print_result(ctx, res)

    return results


def main():
    ctx, _ = _shared.parse_args(
        prog_desc='EdgeDB Databases Benchmark (JS drivers)',
        out_to_json=True)

    print('============ JS ============')
    print(f'concurrency:\t{ctx.concurrency}')
    print(f'warmup time:\t{ctx.warmup_time} seconds')
    print(f'duration:\t{ctx.duration} seconds')
    print(f'queries:\t{", ".join(q for q in ctx.queries)}')
    print(f'benchmarks:\t{", ".join(b for b in ctx.benchmarks)}')
    print()

    data = []
    for benchmark in ctx.benchmarks:
        bench_desc = _shared.BENCHMARKS[benchmark]
        if bench_desc.language != 'js':
            continue

        res = run_bench(ctx, benchmark)
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
            'language': 'js',
            'concurrency': ctx.concurrency,
            'warmup_time': ctx.warmup_time,
            'duration': ctx.duration,
            'data': json_data,
        })
        with open(ctx.json, 'wt') as f:
            f.write(data)


if __name__ == '__main__':
    main()
