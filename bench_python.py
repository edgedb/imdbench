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
import multiprocessing
import os
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
    avg_latency: int
    max_latency: int
    latency_stats: typing.List[int]
    samples: typing.List[str]


class LoopingValues:
    def __init__(self, values):
        self.values = list(values)
        random.shuffle(self.values)
        self.i = 0
        self.len = len(self.values)

    def get_next(self):
        # advance
        self.i += 1
        self.i %= self.len
        return self.values[self.i]


def run_benchmark_method(ctx, benchname, ids, queryname):
    queries_mod = _shared.IMPLEMENTATIONS[benchname].module
    if hasattr(queries_mod, 'init'):
        queries_mod.init(ctx)

    method = getattr(queries_mod, queryname)
    conn = queries_mod.connect(ctx)
    # This is used to loop over input IDs in such a way as to avoid
    # repeating the same ID too closely to itself. This avoid
    # conflicts when concurrently updating the same object.
    id_loop = LoopingValues(ids)

    try:
        samples = []
        nqueries = 0
        latency_stats = np.zeros((math.ceil(ctx.timeout) * 100 * 1000 + 1,))
        min_latency = float('inf')
        max_latency = 0.0

        duration = ctx.warmup_time
        start = time.monotonic()
        while time.monotonic() - start < duration:
            rid = id_loop.get_next()
            method(conn, rid)

        for _ in range(10):
            rid = id_loop.get_next()
            s = method(conn, rid)
            if isinstance(s, bytes):
                s = s.decode()
            samples.append(s)

        duration = ctx.duration
        start = time.monotonic()
        max_req_time = len(latency_stats) - 1
        while time.monotonic() - start < duration:
            rid = id_loop.get_next()
            req_start = time.monotonic_ns()
            try:
                method(conn, rid)
            except Exception as e:
                print("ERROR: ", e)
                continue
            req_time = (time.monotonic_ns() - req_start) // 10000

            if req_time > max_latency:
                max_latency = req_time
            if req_time < min_latency:
                min_latency = req_time

            if req_time > max_req_time:
                req_time = max_req_time
            latency_stats[req_time] += 1

            nqueries += 1

        return nqueries, latency_stats, min_latency, max_latency, samples
    finally:
        queries_mod.close(ctx, conn)


async def run_async_benchmark_method(ctx, benchname, ids, queryname):
    queries_mod = _shared.IMPLEMENTATIONS[benchname].module
    if hasattr(queries_mod, 'init'):
        queries_mod.init(ctx)

    method = getattr(queries_mod, queryname)
    conn = await queries_mod.connect(ctx)
    # This is used to loop over input IDs in such a way as to avoid
    # repeating the same ID too closely to itself. This avoid
    # conflicts when concurrently updating the same object.
    id_loop = LoopingValues(ids)

    try:
        samples = []
        nqueries = 0
        latency_stats = np.zeros((math.ceil(ctx.timeout) * 100 * 1000 + 1,))
        min_latency = float('inf')
        max_latency = 0.0

        duration = ctx.warmup_time
        start = time.monotonic()
        while time.monotonic() - start < duration:
            rid = id_loop.get_next()
            await method(conn, rid)

        for _ in range(10):
            rid = id_loop.get_next()
            s = await method(conn, rid)
            if isinstance(s, bytes):
                s = s.decode()
            samples.append(s)

        duration = ctx.duration
        start = time.monotonic()
        max_req_time = len(latency_stats) - 1
        while time.monotonic() - start < duration:
            rid = id_loop.get_next()
            req_start = time.monotonic_ns()
            await method(conn, rid)
            req_time = (time.monotonic_ns() - req_start) // 10000

            if req_time > max_latency:
                max_latency = req_time
            if req_time < min_latency:
                min_latency = req_time

            if req_time > max_req_time:
                req_time = max_req_time
            latency_stats[req_time] += 1

            nqueries += 1

        return nqueries, latency_stats, min_latency, max_latency, samples
    finally:
        await queries_mod.close(ctx, conn)


def agg_results(results, benchname, queryname, duration) -> Result:
    min_latency = float('inf')
    max_latency = 0.0
    nqueries = 0
    latency_stats = None
    samples = []
    for result in results:
        t_nqueries, t_lat_stats, t_min_latency, t_max_latency, t_samples = \
            result
        samples.append(random.choice(t_samples))
        nqueries += t_nqueries
        if latency_stats is None:
            latency_stats = t_lat_stats
        else:
            latency_stats = np.add(latency_stats, t_lat_stats)
        if t_max_latency > max_latency:
            max_latency = t_max_latency
        if t_min_latency < min_latency:
            min_latency = t_min_latency

    avg_latency = np.average(
        np.arange(len(latency_stats)), weights=latency_stats)

    return Result(
        benchmark=benchname,
        queryname=queryname,
        nqueries=nqueries,
        duration=duration,
        min_latency=min_latency,
        avg_latency=avg_latency,
        max_latency=max_latency,
        latency_stats=latency_stats,
        samples=samples,
    )


def run_benchmark_sync(ctx, benchname, ids, queryname) -> Result:
    method_ids = ids[queryname]
    # We want to split the input ids into separate chunks, so that we
    # avoid concurrent mutations of the same object.
    chunk_len = math.ceil(len(method_ids) / ctx.concurrency)
    with futures.ProcessPoolExecutor(max_workers=ctx.concurrency) as e:
        tasks = []
        for i in range(ctx.concurrency):
            task = e.submit(
                run_benchmark_method,
                ctx,
                benchname,
                method_ids[chunk_len*i:chunk_len*(i+1)],
                queryname)
            tasks.append(task)

        results = [fut.result() for fut in futures.wait(tasks).done]

    return agg_results(results, benchname, queryname, ctx.duration)


def do_run_benchmark_async(ctx, benchname, ids, iproc, queryname) -> Result:
    method_ids = ids[queryname]
    # We want to split the input ids into separate chunks, so that we
    # avoid concurrent mutations of the same object.
    proc_chunk_len = math.ceil(len(method_ids) / ctx.async_split)
    method_ids = method_ids[proc_chunk_len*iproc:proc_chunk_len*(iproc+1)]
    chunk_len = math.ceil(
        len(method_ids) / (ctx.concurrency // ctx.async_split)
    )

    uvloop.install()

    async def run():
        tasks = []
        for i in range(ctx.concurrency // ctx.async_split):
            task = asyncio.create_task(
                run_async_benchmark_method(
                    ctx,
                    benchname,
                    method_ids[chunk_len*i:chunk_len*(i+1)],
                    queryname))
            tasks.append(task)

        return await asyncio.gather(*tasks)

    return asyncio.run(run())


def run_benchmark_async(ctx, benchname, ids, queryname) -> Result:
    # We want to split the input ids into separate chunks, so that we
    # avoid concurrent mutations of the same object.
    with futures.ProcessPoolExecutor(max_workers=ctx.async_split) as e:
        tasks = []
        for i in range(ctx.async_split):
            task = e.submit(
                do_run_benchmark_async,
                ctx,
                benchname,
                ids,
                i,
                queryname)
            tasks.append(task)

        results = [r for fut in futures.wait(tasks).done for r in fut.result()]

    return agg_results(results, benchname, queryname, ctx.duration)


def run_sync(ctx, benchname) -> typing.List[Result]:
    impl = _shared.IMPLEMENTATIONS[benchname]
    queries_mod = impl.module
    results = []

    if impl.extra_env:
        os.environ['IMDBENCH_EXTRA_ENV'] = impl.extra_env
    try:
        if hasattr(queries_mod, 'init'):
            queries_mod.init(ctx)
        idconn = queries_mod.connect(ctx)
        ids = queries_mod.load_ids(ctx, idconn)
        queries_mod.close(ctx, idconn)

        for queryname in ctx.queries:
            # Potentially setup the benchmark state
            conn = queries_mod.connect(ctx)
            queries_mod.setup(ctx, conn, queryname)
            queries_mod.close(ctx, conn)

            res = run_benchmark_sync(ctx, benchname, ids, queryname)
            results.append(res)
            print_result(ctx, res)
            queries_mod.close(ctx, conn)

            # Potentially clean up after the benchmarks
            conn = queries_mod.connect(ctx)
            queries_mod.cleanup(ctx, conn, queryname)
            queries_mod.close(ctx, conn)
    finally:
        os.environ.pop('IMDBENCH_EXTRA_ENV', None)

    return results


def run_async(ctx, benchname) -> typing.List[Result]:
    impl = _shared.IMPLEMENTATIONS[benchname]
    queries_mod = impl.module
    results = []

    async def fetch_ids():
        if hasattr(queries_mod, 'init'):
            queries_mod.init(ctx)
        conn = await queries_mod.connect(ctx)
        try:
            return await queries_mod.load_ids(ctx, conn)
        finally:
            await queries_mod.close(ctx, conn)

    async def setup():
        if not hasattr(queries_mod, 'setup'):
            return
        conn = await queries_mod.connect(ctx)
        try:
            return await queries_mod.setup(ctx, conn, queryname)
        finally:
            await queries_mod.close(ctx, conn)

    async def cleanup():
        if not hasattr(queries_mod, 'cleanup'):
            return
        conn = await queries_mod.connect(ctx)
        try:
            return await queries_mod.cleanup(ctx, conn, queryname)
        finally:
            await queries_mod.close(ctx, conn)

    if impl.extra_env:
        os.environ['IMDBENCH_EXTRA_ENV'] = impl.extra_env
    try:
        uvloop.install()
        ids = asyncio.run(fetch_ids())

        for queryname in ctx.queries:
            # Potentially setup the benchmark state
            asyncio.run(setup())

            res = run_benchmark_async(ctx, benchname, ids, queryname)
            results.append(res)
            print_result(ctx, res)

            # Potentially clean up after the benchmarks
            asyncio.run(cleanup())
    finally:
        os.environ.pop('IMDBENCH_EXTRA_ENV', None)

    return results


def run_bench(ctx, benchname) -> typing.List[Result]:
    queries_mod = _shared.IMPLEMENTATIONS[benchname].module
    if getattr(queries_mod, 'ASYNC', False):
        return run_async(ctx, benchname)
    else:
        return run_sync(ctx, benchname)


def print_result(ctx, result: Result):
    print(f'== {result.benchmark} : {result.queryname} ==')
    print(f'queries:\t{result.nqueries}')
    print(f'qps:\t\t{result.nqueries // ctx.duration} q/s')
    print(f'min latency:\t{result.min_latency / 100:.2f}ms')
    print(f'avg latency:\t{result.avg_latency / 100:.2f}ms')
    print(f'max latency:\t{result.max_latency / 100:.2f}ms')
    print()


def main():
    multiprocessing.set_start_method('spawn')

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
        bench_desc = _shared.IMPLEMENTATIONS[benchmark]
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
                    'latency_stats':
                        [int(i) for i in r.latency_stats.tolist()],
                    'samples': r.samples,
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
