import asyncio
import concurrent.futures as futures
import math
import random
import time
import typing

import numpy as np
import uvloop

from _edgedb import queries as edgedb_queries
from _edgedb import queries_async as edgedb_queries_async
from _edgedb import queries_repack as edgedb_queries_repack
from _django import queries as django_queries
from _django import queries_restfw as django_queries_restfw
from _mongodb import queries as mongodb_queries
from _sqlalchemy import queries as sqlalchemy_queries
from _postgres import queries as postgres_queries
from _postgres import queries_psycopg as postgres_psycopg_queries


class Context(typing.NamedTuple):

    number_of_ids: int
    concurrency: int
    timeout: float


BENCHMARKS = {
    'edgedb': edgedb_queries,
    'edgedb_async': edgedb_queries_async,
    'edgedb_repack': edgedb_queries_repack,

    'django': django_queries,
    'django_restfw': django_queries_restfw,

    'mongodb': mongodb_queries,

    'sqlalchemy': sqlalchemy_queries,

    'postgres': postgres_queries,
    'postgres_psycopg': postgres_psycopg_queries,
}

METHODS = ['get_user', 'get_movie', 'get_person']
METHODS = ['get_person',]


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


def agg_results(results, methodname, duration):
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

    return {
        'method': methodname,
        'nqueries': nqueries,
        'duration': duration,
        'min_latency': min_latency,
        'max_latency': max_latency,
        # 'latency_stats': latency_stats,
    }


def run_benchmark_sync(ctx, benchname, duration, conns, methodname):
    queries_mod = BENCHMARKS[benchname]

    ids = queries_mod.load_ids(ctx, conns[0])
    method_ids = ids[methodname]
    method = getattr(queries_mod, methodname)

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

    return agg_results(results, methodname, duration)


async def run_benchmark_async(ctx, benchname, duration, conns, methodname):
    queries_mod = BENCHMARKS[benchname]

    ids = await queries_mod.load_ids(ctx, conns[0])
    method_ids = ids[methodname]
    method = getattr(queries_mod, methodname)

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
    return agg_results(results, methodname, duration)


def run_sync(ctx, benchname, warmup, duration):
    queries_mod = BENCHMARKS[benchname]

    conns = []
    for i in range(ctx.concurrency):
        conn = queries_mod.connect(ctx)
        conns.append(conn)

    try:
        for methodname in METHODS:
            run_benchmark_sync(
                ctx, benchname, warmup, conns, methodname)
            res = run_benchmark_sync(
                ctx, benchname, duration, conns, methodname)
            print(methodname, res)
    finally:
        for conn in conns:
            queries_mod.close(ctx, conn)


async def run_async(ctx, benchname, warmup, duration):
    queries_mod = BENCHMARKS[benchname]

    conns = []
    for i in range(ctx.concurrency):
        conn = await queries_mod.connect(ctx)
        conns.append(conn)

    try:
        for methodname in METHODS:
            await run_benchmark_async(
                ctx, benchname, warmup, conns, methodname)
            res = await run_benchmark_async(
                ctx, benchname, duration, conns, methodname)
            print(methodname, res)
    finally:
        for conn in conns:
            await queries_mod.close(ctx, conn)


def run(ctx, benchname, warmup, duration):
    print()
    print()
    print(benchname)
    queries_mod = BENCHMARKS[benchname]
    if getattr(queries_mod, 'ASYNC', False):
        uvloop.install()
        return asyncio.run(
            run_async(ctx, benchname, warmup, duration))
    else:
        return run_sync(ctx, benchname, warmup, duration)


ctx = Context(
    number_of_ids=250,
    concurrency=4,
    timeout=2,
)


warmup = 5
duration = 30


# run(ctx, 'edgedb', warmup, duration)
# run(ctx, 'edgedb_repack', warmup, duration) ###### <---------
# run(ctx, 'edgedb_async', warmup, duration)

# run(ctx, 'django', warmup, duration)
# run(ctx, 'django_restfw', warmup, duration)

# run(ctx, 'sqlalchemy', warmup, duration)

# run(ctx, 'mongodb', warmup, duration)

# run(ctx, 'postgres', warmup, duration)
run(ctx, 'postgres_psycopg', warmup, duration)


async def test():

    conn = postgres_psycopg_queries.connect(ctx)
    uid = (postgres_psycopg_queries.load_ids(ctx, conn))['get_person'][20]
    print(postgres_psycopg_queries.get_person(conn, uid))

    print('========')

    # conn = await postgres_queries.connect(ctx)
    # uid = (await postgres_queries.load_ids(ctx, conn))['get_movie'][20]
    # print(await postgres_queries.get_movie(conn, uid))
# asyncio.run(test())

# async def dump_stats():
#     import asyncpg
#     con = await asyncpg.connect(
#         user='edgedb', database='edgedb_bench',
#         port=65027)

#     res = []
#     for r in await con.fetch('''
#             select * from edgedb.pg_stat_statements;
#         '''):
#         if r['calls'] > 1000:
#             res.append(dict(r))

#     import pprint
#     pprint.pprint(res)

# asyncio.run(dump_stats())
