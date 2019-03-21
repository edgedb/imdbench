#!/usr/bin/env python3

#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import asyncio
import concurrent.futures as futures
import json
import math
import random
import time
import typing

import numpy as np
import uvloop

import _shared


class Result(typing.NamedTuple):

    benchmark: str
    queryname: str
    nqueries: int
    duration: int
    min_latency: int
    max_latency: int
    latency_stats: typing.List[int]


def run_benchmark_method(ctx, duration, conn, ids, method):
    nqueries = 0
    latency_stats = np.zeros((math.ceil(ctx.timeout) * 100 * 1000,))
    min_latency = float('inf')
    max_latency = 0.0

    start = time.monotonic()
    while time.monotonic() - start < duration:
        rid = random.choice(ids)
        req_start = time.monotonic_ns()
        method(conn, rid)
        req_time = (time.monotonic_ns() - req_start) // 10000

        if req_time > max_latency:
            max_latency = req_time
        if req_time < min_latency:
            min_latency = req_time
        latency_stats[req_time] += 1
        nqueries += 1

    return nqueries, latency_stats, min_latency, max_latency


async def run_async_benchmark_method(ctx, duration, conn, ids, method):
    nqueries = 0
    latency_stats = np.zeros((math.ceil(ctx.timeout) * 100 * 1000,))
    min_latency = float('inf')
    max_latency = 0.0

    start = time.monotonic()
    while time.monotonic() - start < duration:
        rid = random.choice(ids)
        req_start = time.monotonic_ns()
        await method(conn, rid)
        req_time = (time.monotonic_ns() - req_start) // 10000

        if req_time > max_latency:
            max_latency = req_time
        if req_time < min_latency:
            min_latency = req_time
        latency_stats[req_time] += 1
        nqueries += 1

    return nqueries, latency_stats, min_latency, max_latency


def agg_results(results, benchname, queryname, duration) -> Result:
    min_latency = float('inf')
    max_latency = 0.0
    nqueries = 0
    latency_stats = None
    for result in results:
        t_nqueries, t_latency_stats, t_min_latency, t_max_latency = result
        nqueries += t_nqueries
        if latency_stats is None:
            latency_stats = t_latency_stats
        else:
            latency_stats = np.add(latency_stats, t_latency_stats)
        if t_max_latency > max_latency:
            max_latency = t_max_latency
        if t_min_latency < min_latency:
            min_latency = t_min_latency

    return Result(
        benchmark=benchname,
        queryname=queryname,
        nqueries=nqueries,
        duration=duration,
        min_latency=min_latency,
        max_latency=max_latency,
        latency_stats=latency_stats,
    )


def run_benchmark_sync(ctx, benchname, duration, conns, queryname) -> Result:
    queries_mod = _shared.BENCHMARKS[benchname].module

    ids = queries_mod.load_ids(ctx, conns[0])
    method_ids = ids[queryname]
    method = getattr(queries_mod, queryname)

    with futures.ThreadPoolExecutor(max_workers=ctx.concurrency) as e:
        tasks = []
        for i in range(ctx.concurrency):
            task = e.submit(
                run_benchmark_method,
                ctx,
                duration,
                conns[i],
                method_ids,
                method)
            tasks.append(task)

        results = [fut.result() for fut in futures.wait(tasks).done]

    return agg_results(results, benchname, queryname, duration)


async def run_benchmark_async(ctx, benchname, duration,
                              conns, queryname) -> Result:
    queries_mod = _shared.BENCHMARKS[benchname].module

    ids = await queries_mod.load_ids(ctx, conns[0])
    method_ids = ids[queryname]
    method = getattr(queries_mod, queryname)

    tasks = []
    for i in range(ctx.concurrency):
        task = asyncio.create_task(
            run_async_benchmark_method(
                ctx,
                duration,
                conns[i],
                method_ids,
                method))
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return agg_results(results, benchname, queryname, duration)


def run_sync(ctx, benchname) -> typing.List[Result]:
    queries_mod = _shared.BENCHMARKS[benchname].module
    results = []

    conns = []
    for i in range(ctx.concurrency):
        conn = queries_mod.connect(ctx)
        conns.append(conn)

    try:
        for queryname in ctx.queries:
            run_benchmark_sync(
                ctx, benchname, ctx.warmup_time, conns, queryname)
            res = run_benchmark_sync(
                ctx, benchname, ctx.duration, conns, queryname)
            results.append(res)
            print_result(ctx, res)
    finally:
        for conn in conns:
            queries_mod.close(ctx, conn)

    return results


async def run_async(ctx, benchname) -> typing.List[Result]:
    queries_mod = _shared.BENCHMARKS[benchname].module
    results = []

    conns = []
    for i in range(ctx.concurrency):
        conn = await queries_mod.connect(ctx)
        conns.append(conn)

    try:
        for queryname in ctx.queries:
            await run_benchmark_async(
                ctx, benchname, ctx.warmup_time, conns, queryname)
            res = await run_benchmark_async(
                ctx, benchname, ctx.duration, conns, queryname)
            results.append(res)
            print_result(ctx, res)
    finally:
        for conn in conns:
            await queries_mod.close(ctx, conn)

    return results


def run_bench(ctx, benchname) -> typing.List[Result]:
    queries_mod = _shared.BENCHMARKS[benchname].module
    if getattr(queries_mod, 'ASYNC', False):
        return asyncio.run(run_async(ctx, benchname))
    else:
        return run_sync(ctx, benchname)


def print_result(ctx, result: Result):
    print(f'== {result.benchmark} : {result.queryname} ==')
    print(f'queries:\t{result.nqueries}')
    print(f'min latency:\t{result.min_latency}')
    print(f'max latency:\t{result.max_latency}')
    print()


def main():
    uvloop.install()
    ctx, _ = _shared.parse_args(
        prog_desc='EdgeDB Databases Benchmark (Python drivers)',
        out_to_json=True)

    print('============ Python ============')
    print(f'concurrency:\t{ctx.concurrency}')
    print(f'warmup time:\t{ctx.warmup_time} seconds')
    print(f'duration:\t{ctx.duration} seconds')
    print(f'queries:\t{", ".join(q for q in ctx.queries)}')
    print(f'benchmarks:\t{", ".join(b for b in ctx.benchmarks)}')
    print()

    data = []
    for benchmark in ctx.benchmarks:
        bench_desc = _shared.BENCHMARKS[benchmark]
        if bench_desc.language != 'python':
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
                    'latency_stats': [int(i) for i in r.latency_stats.tolist()]
                })
            json_data.append({
                'benchmark': results[0].benchmark,
                'duration': results[0].duration,
                'queries': json_results,
            })

        data = json.dumps({
            'language': 'python',
            'concurrency': ctx.concurrency,
            'warmup_time': ctx.warmup_time,
            'duration': ctx.duration,
            'data': json_data,
        })
        with open(ctx.json, 'wt') as f:
            f.write(data)


if __name__ == '__main__':
    main()
